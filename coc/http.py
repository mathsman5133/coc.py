"""
MIT License

Copyright (c) 2019-2020 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import logging
import re
import time
import threading

from collections import deque
from datetime import datetime
from itertools import cycle
from time import process_time, perf_counter
from urllib.parse import urlencode

import aiohttp
import requests

from .errors import (
    HTTPException,
    Maintenance,
    NotFound,
    InvalidArgument,
    Forbidden,
    InvalidCredentials,
    GatewayError,
)
from .utils import LRU, HTTPStats

LOG = logging.getLogger(__name__)
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


BASE_URL = "https://api.clashofclans.com/v1"
API_PAGE_BASE_URL = "https://developer.clashofclans.com/api"


def urlify(url, *args, base=BASE_URL, **kwargs):
    parameters = urlencode({k: v for k, v in kwargs.items() if v is not None})
    if parameters:
        return base + url.format(*args).replace("#", "%23") + "?{}".format(parameters)
    else:
        return base + url.format(*args).replace("#", "%23")


async def json_or_text(response):
    """Parses an aiohttp response into a the string or json response."""
    try:
        ret = await response.json()
    except aiohttp.ContentTypeError:
        ret = await response.text(encoding="utf-8")

    return ret


class DevPageSession:
    __slots__ = ("expires_in", "session_id", "api_url", "game_api_token", "scopes")

    def __init__(self, expires_in, session_id, api_url, game_api_token, scopes):
        self.session_id = session_id
        self.expires_in = expires_in
        self.api_url = api_url
        self.game_api_token = game_api_token
        self.scopes = scopes

    @classmethod
    async def async_from_resp(cls, resp):
        data = await json_or_text(resp)

        session = resp.cookies.get("session").value

        expires_in = data["sessionExpiresInSeconds"]
        api_url = data["swaggerUrl"]
        game_api_token = data["temporaryAPIToken"]
        scopes = data["developer"]["allowedScopes"]

        return cls(expires_in, session, api_url, game_api_token, scopes)

    @classmethod
    def from_resp(cls, resp):
        data = resp.json()

        session = resp.cookies.get("session")

        expires_in = data["sessionExpiresInSeconds"]
        api_url = data["swaggerUrl"]
        game_api_token = data["temporaryAPIToken"]
        scopes = data["developer"]["allowedScopes"]

        return cls(expires_in, session, api_url, game_api_token, scopes)

    @property
    def cookies(self):
        return {
            "cookies": "session={};game-api-url={};game-api-token={}".format(self.session_id, self.api_url, self.game_api_token)
        }


class BasicThrottler:
    """Basic throttler that sleeps for `sleep_time` seconds between each request."""

    __slots__ = (
        "sleep_time",
        "last_run",
        "async_lock",
        "sync_lock",
    )

    def __init__(self, sleep_time):
        self.sleep_time = sleep_time
        self.last_run = None
        self.async_lock = asyncio.Lock()
        self.sync_lock = threading.Lock()

    async def __aenter__(self):
        async with self.async_lock:
            last_run = self.last_run
            if last_run:
                difference = process_time() - last_run
                need_to_sleep = self.sleep_time - difference
                if need_to_sleep > 0:
                    LOG.debug("Request throttled. Sleeping for %s", need_to_sleep)
                    await asyncio.sleep(need_to_sleep)

            self.last_run = process_time()
            return self

    async def __aexit__(self, exception_type, exception, traceback):
        pass

    def __enter__(self):
        with self.sync_lock:
            last_run = self.last_run
            if last_run:
                difference = process_time() - last_run
                need_to_sleep = self.sleep_time - difference
                if need_to_sleep > 0:
                    LOG.debug("Request throttled. Sleeping for %s", need_to_sleep)
                    time.sleep(need_to_sleep)

            self.last_run = process_time()
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BatchThrottler:
    """Simple throttler that allows `rate_limit` requests (per second) before sleeping until the next second."""

    __slots__ = (
        "rate_limit",
        "per",
        "retry_interval",
        "_task_logs",
    )

    def __init__(self, rate_limit, per=1.0, retry_interval=0.001):
        self.rate_limit = rate_limit
        self.per = per
        self.retry_interval = retry_interval

        self._task_logs = deque()

    async def __aenter__(self):
        while True:
            now = process_time()

            # Pop items(which are start times) that are no longer in the
            # time window
            while self._task_logs:
                if now - self._task_logs[0] > self.per:
                    self._task_logs.popleft()
                else:
                    break

            # Exit the infinite loop when new task can be processed
            if len(self._task_logs) < self.rate_limit:
                break

            retry_interval = self.retry_interval
            LOG.debug("Request throttled. Sleeping for %s seconds.", retry_interval)
            await asyncio.sleep(retry_interval)

        # Push new task's start time
        self._task_logs.append(process_time())

        return self

    async def __aexit__(self, exception_type, exception, traceback):
        pass

    def __enter__(self):
        while True:
            now = process_time()

            # Pop items(which are start times) that are no longer in the
            # time window
            while self._task_logs:
                if now - self._task_logs[0] > self.per:
                    self._task_logs.popleft()
                else:
                    break

            # Exit the infinite loop when new task can be processed
            if len(self._task_logs) < self.rate_limit:
                break

            retry_interval = self.retry_interval
            LOG.debug("Request throttled. Sleeping for %s seconds.", retry_interval)
            time.sleep(retry_interval)

        # Push new task's start time
        self._task_logs.append(process_time())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class HTTPClientBase:
    """HTTP Client for the library. All low-level requests and key-management occurs here."""

    # pylint: disable=too-many-arguments, missing-docstring, protected-access, too-many-branches
    def __init__(
        self,
        client,
        loop,
        email,
        password,
        key_names,
        key_count,
        key_scopes,
        throttle_limit,
        throttler=BasicThrottler,
        connector=None,
        timeout=30.0,
        cache_max_size=10000,
    ):
        self.client = client
        self.loop = loop
        self.email = email
        self.password = password
        self.key_names = key_names
        self.key_count = key_count
        self.key_scopes = key_scopes
        self.throttle_limit = throttle_limit

        per_second = key_count * throttle_limit

        self.cache = cache_max_size and LRU(cache_max_size)
        self.stats = HTTPStats(max_size=10)

        if issubclass(throttler, BasicThrottler):
            self.throttler = throttler(1 / per_second)
        elif issubclass(throttler, BatchThrottler):
            self.throttler = throttler(per_second)
        else:
            raise TypeError("throttler must be either BasicThrottler or BatchThrottler.")

        self.manage_tokens = True

        self._keys = None  # defined in get_keys()
        self.keys = None  # defined in get_keys()

        self.api_session = None
        self.session = NotImplemented

    def _cache_remove(self, key):
        try:
            del self.cache[key]
        except KeyError:
            pass

    def reset_session(self):
        self.api_session = None

    def request(self, method, url, *args, **kwargs):
        raise NotImplemented

    def get_or_set_session(self):
        raise NotImplemented

    def get_keys(self):
        raise NotImplemented

    def add_keys(self, keys):
        self._keys = keys
        self.keys = cycle(keys)
        self.manage_tokens = False

    # clans

    def search_clans(self, **kwargs):
        return self.request("GET", "/clans", **kwargs)

    def get_clan(self, tag):
        return self.request("GET", "/clans/{}", tag)

    def get_clan_members(self, tag):
        return self.request("GET", "/clans/{}/members", tag)

    def get_clan_warlog(self, tag):
        return self.request("GET", "/clans/{}/warlog", tag)

    def get_clan_current_war(self, tag):
        return self.request("GET", "/clans/{}/currentwar", tag)

    def get_clan_war_league_group(self, tag):
        return self.request("GET", "/clans/{}/currentwar/leaguegroup", tag)

    def get_cwl_wars(self, war_tag):
        return self.request("GET", "/clanwarleagues/wars/{}", war_tag)

    # locations

    def search_locations(self, **kwargs):
        return self.request("GET", "/locations", **kwargs)

    def get_location(self, location_id):
        return self.request("GET", "/locations/{}".format(location_id))

    def get_location_clans(self, location_id, **kwargs):
        return self.request("GET", "/locations/{}/rankings/clans", location_id, **kwargs)

    def get_location_players(self, location_id, **kwargs):
        return self.request("GET", "/locations/{}/rankings/players", location_id, **kwargs)

    def get_location_clans_versus(self, location_id, **kwargs):
        return self.request("GET", "/locations/{}/rankings/clans-versus", location_id, **kwargs)

    def get_location_players_versus(self, location_id, **kwargs):
        return self.request("GET", "/locations/{}/rankings/players-versus", location_id, **kwargs)

    # leagues

    def search_leagues(self, **kwargs):
        return self.request("GET", "/leagues", **kwargs)

    def get_league(self, league_id):
        return self.request("GET", "/leagues/{}", league_id)

    def get_league_seasons(self, league_id, **kwargs):
        return self.request("GET", "/leagues/{}/seasons", league_id, **kwargs)

    def get_league_season_info(self, league_id, season_id, **kwargs):
        return self.request("GET", "/leagues/{}/seasons/{}", league_id, season_id, **kwargs)

    # players

    def get_player(self, player_tag):
        return self.request("GET", "/players/{}", player_tag)

    # labels

    def get_clan_labels(self, **kwargs):
        return self.request("GET", "/labels/clan", **kwargs)

    def get_player_labels(self, **kwargs):
        return self.request("GET", "/labels/players", **kwargs)

    # key management
    # key updating management

    def get_ip(self):
        return self.session.get("https://api.ipify.org/")

    def login_to_site(self, email, password):
        data = {"email": email, "password": password}
        return self.session.post(API_PAGE_BASE_URL + "/login", json=data)

    def find_keys(self, cookies):
        return self.session.post(API_PAGE_BASE_URL + "/apikey/list", cookies=cookies)

    def create_key(self, cookies, scopes, ip):
        data = {
            "name": self.key_names,
            "description": "Created on {}".format(datetime.now().strftime("%c")),
            "cidrRanges": [ip],
            "scopes": [scopes],
        }

        return self.session.post(API_PAGE_BASE_URL + "/apikey/create", cookies=cookies, json=data)

    def delete_key(self, cookies, key_id):
        return self.session.post(API_PAGE_BASE_URL + "/apikey/revoke", json={"id": key_id}, cookies=cookies)


class HTTPClient(HTTPClientBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.timeout = kwargs.pop('timeout', 30.0)

        self.get_session_lock = threading.Lock()
        self.lock = threading.Semaphore(self.key_count * self.throttle_limit)
        self.session = requests.Session()

    def close(self):
        self.session.close()

    def request(self, method, url, *args, **kwargs):
        stats_url = url

        url = urlify(url, *args, **kwargs)
        key = next(self.keys)

        headers = {
            "Accept": "application/json",
            "authorization": "Bearer {}".format(key),
        }

        cache = self.cache
        # the cache will be cleaned once it becomes stale / a new object is available from the api.
        if cache is not None:
            try:
                return cache[url]
            except KeyError:
                pass

        for tries in range(5):
            try:
                with self.lock, self.throttler:
                    start = perf_counter()
                    response = self.session.request(method, url, timeout=self.timeout, headers=headers)
                    self.stats[stats_url] = (perf_counter() - start) * 1000

                    LOG.debug("Received status code %s for url %s", response.status_code, url)
                    try:
                        data = response.json()
                    except ValueError:
                        data = response.text

                    try:
                        # set a callback to remove the item from cache once it's stale.
                        delta = int(response.headers["Cache-Control"].strip("max-age="))
                        data["_response_retry"] = delta
                        if cache is not None:
                            self.cache[url] = data
                            LOG.debug("Cache-Control max age: %s seconds, key: %s", delta, url)
                            self.loop.call_later(delta, self._cache_remove, url)

                    except (KeyError, AttributeError, ValueError):
                        # the request didn't contain cache control headers so skip any cache handling.
                        # if the API returns a timeout error (504) it will return a string of HTML.
                        if isinstance(data, dict):
                            data["_response_retry"] = 0

                    if 200 <= response.status_code < 300:
                        LOG.debug("%s has received %s", url, data)
                        return data

                    if response.status_code == 400:
                        raise InvalidArgument(response, data)

                    if response.status_code == 403:
                        if data.get("reason") == "accessDenied.invalidIp" and self.manage_tokens is True:
                            self.reset_key(key)
                            LOG.info("Reset Clash of Clans key")
                            return self.request(method, url)

                        raise Forbidden(response, data)

                    if response.status_code == 404:
                        raise NotFound(response, data)
                    if response.status_code == 429:
                        LOG.error(
                            "We have been rate-limited by the API. "
                            "Reconsider the number of requests you are allowing per second."
                        )
                        raise HTTPException(response, data)

                    if response.status_code == 503:
                        if isinstance(data, str):
                            # weird case where a 503 will be raised, but html returned.
                            text = re.compile(r"<[^>]+>").sub(data, "")
                            raise Maintenance(response, text)

                        raise Maintenance(response, data)

                    if response.status_code in (500, 502, 504):
                        # gateway error, retry again
                        time.sleep(tries * 2 + 1)
                        continue

            except requests.exceptions.Timeout:
                # api timed out, retry again
                if tries > 3:
                    raise GatewayError("The API timed out waiting for the request.")

                time.sleep(tries * 2 + 1)
                continue
            raise

        else:
            if response.status_code in (500, 502, 504):
                # gateway errors return HTML
                text = re.compile(r"<[^>]+>").sub(data, "")
                raise GatewayError(response, text)

            raise HTTPException(response, data)

    def get_or_set_session(self):
        with self.get_session_lock:
            if self.api_session is None:
                resp = self.login_to_site(self.email, self.password)
                self.api_session = DevPageSession.from_resp(resp)
                self.loop.call_later(self.api_session.expires_in, self.reset_session)

            return self.api_session

    def get_keys(self):
        session = self.get_or_set_session()
        ip = self.get_ip().text
        data = self.find_keys(session.cookies).json()
        current_keys = data["keys"]

        self._keys = [key["key"] for key in current_keys if key["name"] == self.key_names and ip in key["cidrRanges"]]

        required_key_count = self.key_count
        current_key_count = len(current_keys)

        if required_key_count > len(self._keys):
            for key in (k for k in current_keys if k["name"] == self.key_names and ip not in k["cidrRanges"]):
                try:
                    self.delete_key(session.cookies, key["id"])
                except (InvalidArgument, NotFound):
                    continue
                else:
                    new = self.create_key(session.cookies, session.scopes, ip)
                    self._keys.append(new)
                    self.client.dispatch("on_key_reset", new)

            make_keys = required_key_count - len(self._keys)
            for _ in range(make_keys):
                if current_key_count >= KEY_MAXIMUM:
                    break

                new = self.create_key(session.cookies, session.scopes, ip).json()["key"]["key"]
                self._keys.append(new)
                self.client.dispatch("on_key_reset", new)
                current_key_count += 1

            if current_key_count == KEY_MAXIMUM and len(self._keys) < required_key_count:
                LOG.critical("%s keys were requested to be used, but a maximum of %s could be "
                             "found/made on the developer site, as it has a maximum of 10 keys per account. "
                             "Please delete some keys or lower your `key_count` level."
                             "I will use %s keys for the life of this client.",
                             required_key_count, current_key_count, current_key_count)

        if len(self._keys) == 0:
            self.close()
            raise RuntimeError(
                "There are {} API keys already created and none match a key_name of '{}'."
                "Please specify a key_name kwarg, or go to 'https://developer.clashofclans.com' to delete "
                "unused keys.".format(current_key_count, self.key_names)
            )

        self.keys = cycle(self._keys)

    def reset_key(self, key):
        session = self.get_or_set_session()
        data = self.find_keys(session.cookies).json()
        try:
            existing_keys = data["keys"]
        except (TypeError, KeyError):
            # long standing bug where the dev site doesn't give a proper return dict when
            # multiple concurrent logins are made. this is just a safety net, hopefully one of
            # the requests will work.
            return

        key_id = [t["id"] for t in existing_keys if t["key"] == key]

        try:
            self.delete_key(session.cookies, key_id)
        except (InvalidArgument, NotFound):
            return

        new_key = self.create_key(session.cookies, session.scopes, self.get_ip().text)

        # this is to prevent reusing an already used keys.
        # All it does is move the current key to the front,
        # by moving any already used ones to the end so
        # we keep the original key order moving forward.
        keys = self._keys
        key_index = keys.index(key)
        self._keys = keys[key_index:] + keys[:key_index]

        # now we can set the new key which is the first
        # one in self._keys, then start the cycle over.
        self._keys[0] = new_key
        self.keys = cycle(self._keys)
        self.client.dispatch("key_reset", new_key)


class AsyncHTTPClient(HTTPClientBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.get_session_lock = asyncio.Lock()
        self.lock = asyncio.Semaphore(self.key_count * self.throttle_limit)
        self.session = aiohttp.ClientSession(connector=kwargs.pop('connector', None), timeout=aiohttp.ClientTimeout(total=kwargs.pop('timeout', 30.0)))

    async def close(self):
        await self.session.close()

    async def request(self, method, url, *args, **kwargs):
        stats_url = url

        url = urlify(url, *args, **kwargs)
        key = next(self.keys)

        headers = {
            "Accept": "application/json",
            "authorization": "Bearer {}".format(key),
        }

        cache = self.cache
        # the cache will be cleaned once it becomes stale / a new object is available from the api.
        if cache is not None:
            try:
                return cache[url]
            except KeyError:
                pass

        for tries in range(5):
            try:
                async with self.lock, self.throttler:
                    start = perf_counter()
                    async with self.session.request(method, url, headers=headers) as response:
                        self.stats[stats_url] = (perf_counter() - start) * 1000

                        LOG.debug("Received status code %s for url %s", response.status, url)
                        data = await json_or_text(response)

                        try:
                            # set a callback to remove the item from cache once it's stale.
                            delta = int(response.headers["Cache-Control"].strip("max-age="))
                            data["_response_retry"] = delta
                            if cache is not None:
                                self.cache[url] = data
                                LOG.debug("Cache-Control max age: %s seconds, key: %s", delta, url)
                                self.loop.call_later(delta, self._cache_remove, url)

                        except (KeyError, AttributeError, ValueError):
                            # the request didn't contain cache control headers so skip any cache handling.
                            # if the API returns a timeout error (504) it will return a string of HTML.
                            if isinstance(data, dict):
                                data["_response_retry"] = 0

                        if 200 <= response.status < 300:
                            LOG.debug("%s has received %s", url, data)
                            return data

                        if response.status == 400:
                            raise InvalidArgument(response, data)

                        if response.status == 403:
                            if data.get("reason") == "accessDenied.invalidIp" and self.manage_tokens is True:
                                await self.reset_key(key)
                                LOG.info("Reset Clash of Clans key")
                                return await self.request(method, url)

                            raise Forbidden(response, data)

                        if response.status == 404:
                            raise NotFound(response, data)
                        if response.status == 429:
                            LOG.error(
                                "We have been rate-limited by the API. "
                                "Reconsider the number of requests you are allowing per second."
                            )
                            raise HTTPException(response, data)

                        if response.status == 503:
                            if isinstance(data, str):
                                # weird case where a 503 will be raised, but html returned.
                                text = re.compile(r"<[^>]+>").sub(data, "")
                                raise Maintenance(response, text)

                            raise Maintenance(response, data)

                        if response.status in (500, 502, 504):
                            # gateway error, retry again
                            await asyncio.sleep(tries * 2 + 1)
                            continue

            except asyncio.TimeoutError:
                # api timed out, retry again
                if tries > 3:
                    raise GatewayError("The API timed out waiting for the request.")

                await asyncio.sleep(tries * 2 + 1)
                continue
            raise

        else:
            if response.status in (500, 502, 504):
                # gateway errors return HTML
                text = re.compile(r"<[^>]+>").sub(data, "")
                raise GatewayError(response, text)

            raise HTTPException(response, data)

    async def get_data_from_url(self, url):
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.read()
            if response.status == 404:
                raise NotFound(response, "image not found")

            raise HTTPException(response, "failed to get image")

    async def get_or_set_session(self):
        async with self.get_session_lock:
            if self.api_session is None:
                resp = await self.login_to_site(self.email, self.password)
                self.api_session = await DevPageSession.async_from_resp(resp)
                self.loop.call_later(self.api_session.expires_in, self.reset_session)

            return self.api_session

    async def get_keys(self):
        self.client._ready.clear()

        session = await self.get_or_set_session()
        ip = await json_or_text(await self.get_ip())
        data = await json_or_text(await self.find_keys(session.cookies))
        current_keys = data["keys"]

        self._keys = [key["key"] for key in current_keys if key["name"] == self.key_names and ip in key["cidrRanges"]]

        required_key_count = self.key_count
        current_key_count = len(current_keys)

        if required_key_count > len(self._keys):
            for key in (k for k in current_keys if k["name"] == self.key_names and ip not in k["cidrRanges"]):
                try:
                    await self.delete_key(session.cookies, key["id"])
                except (InvalidArgument, NotFound):
                    continue
                else:
                    new = await self.create_key(session.cookies, session.scopes, ip)
                    self._keys.append(new)
                    self.client.dispatch("on_key_reset", new)

            make_keys = required_key_count - len(self._keys)
            for _ in range(make_keys):
                if current_key_count >= KEY_MAXIMUM:
                    break

                resp = await self.create_key(session.cookies, session.scopes, ip)
                new = (await json_or_text(resp))["key"]["key"]
                self._keys.append(new)
                self.client.dispatch("on_key_reset", new)
                current_key_count += 1

            if current_key_count == KEY_MAXIMUM and len(self._keys) < required_key_count:
                LOG.critical("%s keys were requested to be used, but a maximum of %s could be "
                             "found/made on the developer site, as it has a maximum of 10 keys per account. "
                             "Please delete some keys or lower your `key_count` level."
                             "I will use %s keys for the life of this client.",
                             required_key_count, current_key_count, current_key_count)

        if len(self._keys) == 0:
            await self.close()
            raise RuntimeError(
                "There are {} API keys already created and none match a key_name of '{}'."
                "Please specify a key_name kwarg, or go to 'https://developer.clashofclans.com' to delete "
                "unused keys.".format(current_key_count, self.key_names)
            )

        self.keys = cycle(self._keys)
        self.client._ready.set()

    async def reset_key(self, key):
        session = await self.get_or_set_session()
        data = await json_or_text(await self.find_keys(session.cookies))
        try:
            existing_keys = data["keys"]
        except (TypeError, KeyError):
            # long standing bug where the dev site doesn't give a proper return dict when
            # multiple concurrent logins are made. this is just a safety net, hopefully one of
            # the requests will work.
            return

        key_id = [t["id"] for t in existing_keys if t["key"] == key]

        try:
            await self.delete_key(session.cookies, key_id)
        except (InvalidArgument, NotFound):
            return

        new_key = await self.create_key(session.cookies, session.scopes, await json_or_text(await self.get_ip()))

        # this is to prevent reusing an already used keys.
        # All it does is move the current key to the front,
        # by moving any already used ones to the end so
        # we keep the original key order moving forward.
        keys = self._keys
        key_index = keys.index(key)
        self._keys = keys[key_index:] + keys[:key_index]

        # now we can set the new key which is the first
        # one in self._keys, then start the cycle over.
        self._keys[0] = new_key
        self.keys = cycle(self._keys)
        self.client.dispatch("key_reset", new_key)

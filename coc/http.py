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

from collections import deque
from datetime import datetime
from itertools import cycle
from time import process_time, perf_counter
from typing import Optional
from urllib.parse import urlencode
from base64 import b64decode as base64_b64decode
from json import loads as json_loads

import aiohttp

from .errors import (
    HTTPException,
    Maintenance,
    NotFound,
    InvalidArgument,
    Forbidden,
    InvalidCredentials,
    GatewayError,
)
from .utils import FIFO, HTTPStats

LOG = logging.getLogger(__name__)
KEY_MINIMUM, KEY_MAXIMUM = 1, 10
stats_url_matcher = re.compile(r"%23[\da-zA-Z]+|\d{8,}|global")


async def json_or_text(response):
    """Parses an aiohttp response into a the string or json response."""
    try:
        ret = await response.json()
    except aiohttp.ContentTypeError:
        ret = await response.text(encoding="utf-8")

    return ret


class BasicThrottler:
    """Basic throttler that sleeps for `sleep_time` seconds between each request."""

    __slots__ = (
        "sleep_time",
        "last_run",
        "lock",
    )

    def __init__(self, sleep_time):
        self.sleep_time = sleep_time
        self.last_run = None
        self.lock = asyncio.Lock()
        LOG.debug("BasicThrottler initialized with sleeptime %s", self.sleep_time)

    async def __aenter__(self):
        async with self.lock:
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
        LOG.debug("BatchThrottler initialized with rate_limit %s, per %s, retry_interval %s", self.rate_limit, self.per,
                  self. retry_interval)

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


class Route:
    """Helper class to create endpoint URLs."""
    ignored_kwargs = ['lookup_cache', 'update_cache', 'ignore_cached_errors']

    def __init__(self, method: str, base: str, path: str, **kwargs: dict):
        """
        The class is used to create the final URL used to fetch the data
        from the API. The parameters that are passed to the API are all in
        the GET request packet. This class will parse the `kwargs` dictionary
        and concatenate any parameters passed in.

        Parameters
        ----------
        method:
            :class:`str`: HTTP method used for the HTTP request
        base:
            :class:`str`: Base URL used for the HTTP request
        path:
            :class:`str`: URL path used for the HTTP request
        kwargs:
            :class:`dict`: Optional options used to concatenate into the final
            URL
        """
        if "#" in path:
            path = path.replace("#", "%23")

        self.method = method
        self.path = path
        self.base = base

        url = self.base + self.path

        if kwargs:
            url_params = {}
            for k, v in kwargs.items():
                if v is None:
                    continue
                if k in self.ignored_kwargs:
                    continue
                url_params[k] = v
            self.url = "{}?{}".format(url, urlencode(url_params))
        else:
            self.url = url

    @property
    def stats_key(self):
        return stats_url_matcher.sub("{}", self.path)


class HTTPClient:
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
            cache_max_size=10000,
            stats_max_size=1000,
            base_url="https://api.clashofclans.com/v1",
            ip=None,
            lookup_cache=True,
            update_cache=True,
            ignore_cached_errors=None,
    ):
        self.aiohttp_request_kwargs = ['params', 'data', 'json', 'cookies', 'headers', 'skip_auto_headers',
                                       'auth', 'allow_redirects', 'max_redirects', 'compress', 'chunked', 'expect100',
                                       'raise_for_status', 'read_until_eof', 'proxy', 'proxy_auth', 'timeout',
                                       'ssl', 'server_hostname', 'proxy_headers', 'trace_request_ctx', 'read_bufsize',
                                       'auto_decompress', 'max_line_size', 'max_field_size']
        self.client = client
        self.loop = loop
        self.email = email
        self.password = password
        self.key_names = key_names
        self.key_count = key_count
        self.key_scopes = key_scopes
        self.throttle_limit = throttle_limit
        per_second = key_count * throttle_limit
        self.lookup_cache = lookup_cache
        self.update_cache = update_cache
        self.ignore_cached_errors = ignore_cached_errors or []
        self.__session: Optional[aiohttp.ClientSession] = None
        self.__lock = asyncio.Semaphore(per_second)
        self.cache = cache_max_size and FIFO(cache_max_size)
        self._cache_remove_count = 0
        self.stats = stats_max_size and HTTPStats(max_size=stats_max_size)
        if base_url and isinstance(base_url, str) and len(base_url) > 0:
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            self.base_url = base_url
        else:
            raise ValueError("base_url must be a string and not empty.")
        self.ip = ip
        if issubclass(throttler, BasicThrottler):
            self.__throttle = throttler(1 / per_second)
        elif issubclass(throttler, BatchThrottler):
            self.__throttle = throttler(per_second)
        else:
            raise TypeError("throttler must be either BasicThrottler or BatchThrottler.")

        self._keys = []
        self.keys = None

        self.initialising_keys = asyncio.Event()
        self.initialising_keys.set()

    def _cache_remove(self, key):
        try:
            del self.cache[key]
            #  The following fixes a memory leak that is caused by python dicts not properly freeing disk space
            self._cache_remove_count += 1
            if self._cache_remove_count >= self.cache.max_size:
                self.cache = self.cache.copy()
                self._cache_remove_count = 0
                LOG.debug("Cache copied to prevent a memory leak")
        except KeyError:
            pass

    async def create_session(self, connector, timeout):
        self.__session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=timeout))

    async def close(self):
        if self.__session:
            await self.__session.close()

    async def request(self, route, **kwargs):
        method = route.method
        url = route.url

        headers = {
            "Accept"       : "application/json",
            "authorization": "Bearer {}".format(next(self.keys)),
            "Accept-Encoding": "gzip, deflate",
        }
        kwargs["headers"] = headers

        if "json" in kwargs:
            kwargs["headers"]["Content-Type"] = "application/json"

        cache_control_key = route.url
        cache = self.cache
        lookup_cache = kwargs.pop("lookup_cache", self.lookup_cache)
        update_cache = kwargs.pop("update_cache", self.update_cache)
        ignore_cached_errors = kwargs.pop("ignore_cached_errors", self.ignore_cached_errors)
        # the cache will be cleaned once it becomes stale / a new object is available from the api.
        if isinstance(cache, FIFO) and (lookup_cache or (lookup_cache is None and 'realtime' not in url)):
            try:
                data = cache[cache_control_key]
                status_code = data.get("status_code")
                if data.get("timestamp") and data.get("timestamp") + data.get("_response_retry", 0) < datetime.utcnow().timestamp():
                    self._cache_remove(cache_control_key)
                elif not status_code or 200 <= status_code < 300:
                    return data
                # ignore status cached errors if wanted
                elif isinstance(ignore_cached_errors, list) and status_code in ignore_cached_errors:
                    pass
                elif status_code == 400:
                    raise InvalidArgument(400, data)
                elif status_code == 403:
                    raise Forbidden(403, data)
                elif status_code == 404:
                    raise NotFound(404, data)
                elif status_code == 503:
                    raise Maintenance(503, data)
            except KeyError:
                pass
        request_kwargs = {k: v for k, v in kwargs.items() if k in self.aiohttp_request_kwargs}
        for tries in range(5):
            try:
                async with self.__lock, self.__throttle:
                    start = perf_counter()
                    async with self.__session.request(method, url, **request_kwargs) as response:

                        perf = (perf_counter() - start) * 1000
                        log_info = {"method": method, "url": url, "perf_counter": perf, "status": response.status}
                        if isinstance(self.stats, HTTPStats):
                            self.stats[route.stats_key] = perf

                        LOG.debug("API HTTP Request: %s", str(log_info))
                        data = (await json_or_text(response)) or {}
                        data["status_code"] = response.status
                        data["timestamp"] = datetime.utcnow().timestamp()
                        try:
                            # set a callback to remove the item from cache once it's stale.
                            delta = int(response.headers["Cache-Control"].strip("max-age=").strip("public max-age="))
                            # encounter for changed description in cache control header. for realtime it is always
                            # 600 but that is not true. Correct is 0
                            data["_response_retry"] = delta if 'realtime' not in url else 0
                            if isinstance(cache, FIFO) and (update_cache or (update_cache is None and 'realtime' not in url)):
                                self.cache[cache_control_key] = data
                                LOG.debug("Cache-Control max age: %s seconds, key: %s", delta, cache_control_key)
                                self.loop.call_later(delta, self._cache_remove, cache_control_key)

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
                            LOG.info("forbidden! resp: %s, msg: %s", str(response), str(data))
                            if data.get("reason") == "accessDenied.invalidIp" and self.email and self.password:
                                if self.initialising_keys.is_set():
                                    await self.initialise_keys()

                                await self.initialising_keys.wait()
                                return await self.request(route, **kwargs)

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

                        # catch any stray status codes
                        raise HTTPException(response, data)

            except asyncio.TimeoutError:
                # api timed out, retry again
                if tries > 3:
                    raise GatewayError("The API timed out waiting for the request.")

                await asyncio.sleep(tries * 2 + 1)
                continue

        else:
            if response.status in (500, 502, 504):
                if isinstance(data, str):
                    # gateway errors return HTML
                    text = re.compile(r"<[^>]+>").sub(data, "")
                    raise GatewayError(response, text)

                raise GatewayError(response, data)

            raise HTTPException(response, data)

    # clans

    def search_clans(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans", **kwargs), **kwargs)

    def get_clan(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}".format(tag)), **kwargs)

    def get_clan_members(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/members".format(tag), **kwargs), **kwargs)

    def get_clan_war_log(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/warlog".format(tag), **kwargs), **kwargs)

    def get_clan_current_war(self, tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/currentwar".format(tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_clan_war_league_group(self, tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/currentwar/leaguegroup".format(tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_cwl_wars(self, war_tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clanwarleagues/wars/{}".format(war_tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_clan_raid_log(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/capitalraidseasons".format(tag), **kwargs), **kwargs)

    # locations

    def search_locations(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations", **kwargs), **kwargs)

    def get_location(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}".format(location_id)), **kwargs)

    def get_location_clans(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/clans".format(location_id), **kwargs), **kwargs)

    def get_location_players(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/players".format(location_id), **kwargs), **kwargs)

    def get_location_clans_builder_base(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/clans-builder-base".format(location_id), **kwargs),
                            **kwargs)

    def get_location_clans_capital(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/capitals".format(location_id), **kwargs), **kwargs)

    def get_location_players_builder_base(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/players-builder-base".format(location_id), **kwargs),
                            **kwargs)

    # leagues

    def search_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues", **kwargs), **kwargs)

    def search_capital_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/capitalleagues", **kwargs), **kwargs)

    def search_war_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/warleagues", **kwargs), **kwargs)

    def search_builder_base_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/builderbaseleagues", **kwargs), **kwargs)

    def get_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}".format(league_id)), **kwargs)

    def get_capital_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/capitalleagues/{}".format(league_id)), **kwargs)

    def get_war_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/warleagues/{}".format(league_id)), **kwargs)

    def get_builder_base_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/builderbaseleagues/{}".format(league_id)), **kwargs)

    def get_league_seasons(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}/seasons".format(league_id), **kwargs), **kwargs)

    def get_league_season_info(self, league_id, season_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}/seasons/{}".format(league_id, season_id), **kwargs),
                            **kwargs)

    # players

    def get_player(self, player_tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/players/{}".format(player_tag)), **kwargs)

    def verify_player_token(self, player_tag, token, **kwargs):
        return self.request(Route("POST", self.base_url, "/players/{}/verifytoken".format(player_tag)),
                            json={"token": token}, **kwargs)

    # labels

    def get_clan_labels(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/labels/clan", **kwargs), **kwargs)

    def get_player_labels(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/labels/players", **kwargs), **kwargs)

    def get_current_goldpass_season(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/goldpass/seasons/current"), **kwargs)

    # key updating management

    async def initialise_keys(self):
        LOG.debug("Initialising keys from the developer site.")
        self.initialising_keys.clear()

        # Use context manager to automatically clean up after ourselves
        async with aiohttp.ClientSession() as session:
            body = {"email": self.email, "password": self.password}
            resp = await session.post("https://developer.clashofclans.com/api/login", json=body)
            if resp.status == 403:
                LOG.error("Invalid credentials used when attempting to log in")
                await self.close()
                raise InvalidCredentials()

            LOG.info("Successfully logged into the developer site.")

            resp_payload = await resp.json()
            if not self.ip:
                ip = json_loads(base64_b64decode(resp_payload["temporaryAPIToken"].split(".")[1] + "====").decode("utf-8"))["limits"][1]["cidrs"][0].split("/")[0]
            else:
                ip = self.ip
            LOG.info("Found IP address to be %s", ip)

            resp = await session.post("https://developer.clashofclans.com/api/apikey/list")
            keys = (await resp.json())["keys"]
            for key in keys:
                LOG.debug(f"Key {key}")
                if key["name"] != self.key_names or ip not in key["cidrRanges"]:
                    continue
                self._keys.append(key["key"])
                if len(self._keys) == self.key_count:
                    break

            LOG.info("Retrieved %s valid keys from the developer site.", len(self._keys))

            if len(self._keys) < self.key_count:
                for key in keys[:]:
                    if key["name"] != self.key_names or ip in key["cidrRanges"]:
                        continue
                    LOG.info(
                            "Deleting key with the name %s and IP %s (not matching our current IP address).",
                            self.key_names, key["cidrRanges"],
                    )
                    resp = await session.post("https://developer.clashofclans.com/api/apikey/revoke", json={"id": key["id"]})
                    if resp.status == 200:
                        keys.remove(key)

                while len(self._keys) < self.key_count and len(keys) < KEY_MAXIMUM:
                    data = {
                        "name"       : self.key_names,
                        "description": "Created on {}".format(datetime.now().strftime("%c")),
                        "cidrRanges" : [ip],
                        "scopes"     : [self.key_scopes],
                    }

                    LOG.info("Creating key with data %s.", str(data))

                    resp = await session.post("https://developer.clashofclans.com/api/apikey/create", json=data)
                    key = await resp.json()

                    if resp.status != 200:
                        LOG.error(key.get("description"))
                        raise ValueError(key.get("description"))

                    self._keys.append(key["key"]["key"])

            if len(keys) == 10 and len(self._keys) < self.key_count:
                LOG.critical("%s keys were requested to be used, but a maximum of %s could be "
                             "found/made on the developer site, as it has a maximum of 10 keys per account. "
                             "Please delete some keys or lower your `key_count` level."
                             "I will use %s keys for the life of this client.",
                             self.key_count, len(self._keys), len(self._keys))

            if len(self._keys) == 0:
                await self.close()
                raise RuntimeError(
                        "There are {} API keys already created and none match a key_name of '{}'."
                        "Please specify a key_name kwarg, or go to 'https://developer.clashofclans.com' to delete "
                        "unused keys.".format(len(keys), self.key_names)
                )

        self.keys = cycle(self._keys)
        self.initialising_keys.set()
        LOG.info("Successfully initialised keys for use.")

    async def get_data_from_url(self, url):
        async with self.__session.get(url) as response:
            if response.status == 200:
                return await response.read()
            if response.status == 404:
                raise NotFound(response, "image not found")

            raise HTTPException(response, "failed to get image")

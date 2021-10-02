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
from urllib.parse import urlencode

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
from .utils import LRU, HTTPStats

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

    BASE = "https://api.clashofclans.com/v1"

    def __init__(self, method, path: str, **kwargs):
        if "#" in path:
            path = path.replace("#", "%23")

        self.method = method
        self.path = path
        url = self.BASE + self.path

        if kwargs:
            self.url = "{}?{}".format(url, urlencode({k: v for k, v in kwargs.items() if v is not None}))
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

        self.__session = None
        self.__lock = asyncio.Semaphore(per_second)
        self.cache = cache_max_size and LRU(cache_max_size)
        self.stats = stats_max_size and HTTPStats(max_size=stats_max_size)

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
            "Accept": "application/json",
            "authorization": "Bearer {}".format(next(self.keys)),
        }
        kwargs["headers"] = headers

        if "json" in kwargs:
            kwargs["headers"]["Content-Type"] = "application/json"

        cache_control_key = route.url
        cache = self.cache
        # the cache will be cleaned once it becomes stale / a new object is available from the api.
        if cache is not None:
            try:
                return cache[cache_control_key]
            except KeyError:
                pass

        for tries in range(5):
            try:
                async with self.__lock, self.__throttle:
                    start = perf_counter()
                    async with self.__session.request(method, url, **kwargs) as response:

                        perf = (perf_counter() - start) * 1000
                        log_info = {"method": method, "url": url, "perf_counter": perf, "status": response.status}
                        if self.stats:
                            self.stats[route.stats_key] = perf

                        LOG.debug("API HTTP Request: %s", str(log_info))
                        data = await json_or_text(response)

                        try:
                            # set a callback to remove the item from cache once it's stale.
                            delta = int(response.headers["Cache-Control"].strip("max-age="))
                            data["_response_retry"] = delta
                            if cache is not None:
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

            except asyncio.TimeoutError:
                # api timed out, retry again
                if tries > 3:
                    raise GatewayError("The API timed out waiting for the request.")

                await asyncio.sleep(tries * 2 + 1)
                continue
            raise

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
        return self.request(Route("GET", "/clans", **kwargs))

    def get_clan(self, tag):
        return self.request(Route("GET", "/clans/{}".format(tag)))

    def get_clan_members(self, tag):
        return self.request(Route("GET", "/clans/{}/members".format(tag)))

    def get_clan_warlog(self, tag):
        return self.request(Route("GET", "/clans/{}/warlog".format(tag)))

    def get_clan_current_war(self, tag):
        return self.request(Route("GET", "/clans/{}/currentwar".format(tag)))

    def get_clan_war_league_group(self, tag):
        return self.request(Route("GET", "/clans/{}/currentwar/leaguegroup".format(tag)))

    def get_cwl_wars(self, war_tag):
        return self.request(Route("GET", "/clanwarleagues/wars/{}".format(war_tag)))

    # locations

    def search_locations(self, **kwargs):
        return self.request(Route("GET", "/locations", **kwargs))

    def get_location(self, location_id):
        return self.request(Route("GET", "/locations/{}".format(location_id)))

    def get_location_clans(self, location_id, **kwargs):
        return self.request(Route("GET", "/locations/{}/rankings/clans".format(location_id), **kwargs))

    def get_location_players(self, location_id, **kwargs):
        return self.request(Route("GET", "/locations/{}/rankings/players".format(location_id), **kwargs))

    def get_location_clans_versus(self, location_id, **kwargs):
        return self.request(Route("GET", "/locations/{}/rankings/clans-versus".format(location_id), **kwargs))

    def get_location_players_versus(self, location_id, **kwargs):
        return self.request(Route("GET", "/locations/{}/rankings/players-versus".format(location_id), **kwargs))

    # leagues

    def search_leagues(self, **kwargs):
        return self.request(Route("GET", "/leagues", **kwargs))

    def get_league(self, league_id):
        return self.request(Route("GET", "/leagues/{}".format(league_id)))

    def get_league_seasons(self, league_id, **kwargs):
        return self.request(Route("GET", "/leagues/{}/seasons".format(league_id), **kwargs))

    def get_league_season_info(self, league_id, season_id, **kwargs):
        return self.request(Route("GET", "/leagues/{}/seasons/{}".format(league_id, season_id), **kwargs))

    # players

    def get_player(self, player_tag):
        return self.request(Route("GET", "/players/{}".format(player_tag)))

    def verify_player_token(self, player_tag, token):
        return self.request(Route("POST", "/players/{}/verifytoken".format(player_tag)), json={"token": token})

    # labels

    def get_clan_labels(self, **kwargs):
        return self.request(Route("GET", "/labels/clan", **kwargs))

    def get_player_labels(self, **kwargs):
        return self.request(Route("GET", "/labels/players", **kwargs))

    # key updating management

    async def initialise_keys(self):
        LOG.debug("Initialising keys from the developer site.")
        self.initialising_keys.clear()
        session = aiohttp.ClientSession()

        body = {"email": self.email, "password": self.password}
        resp = await session.post("https://developer.clashofclans.com/api/login", json=body)
        if resp.status == 403:
            raise InvalidCredentials(resp)

        LOG.info("Successfully logged into the developer site.")

        resp = await session.get("https://api.ipify.org/")
        ip = await resp.text()

        LOG.info("Found IP address to be %s", ip)

        resp = await session.post("https://developer.clashofclans.com/api/apikey/list")
        keys = (await resp.json())["keys"]
        self._keys.extend(key["key"] for key in keys if key["name"] == self.key_names and ip in key["cidrRanges"])

        LOG.info("Retrieved %s valid keys from the developer site.", len(self._keys))

        if len(self._keys) < self.key_count:
            for key in (k for k in keys if k["name"] == self.key_names and ip not in k["cidrRanges"]):
                LOG.info(
                    "Deleting key with the name %s and IP %s (not matching our current IP address).",
                    self.key_names, key["cidrRanges"],
                )
                await session.post("https://developer.clashofclans.com/api/apikey/revoke", json={"id": key["id"]})

            while len(self._keys) < self.key_count and len(keys) < KEY_MAXIMUM:
                data = {
                    "name": self.key_names,
                    "description": "Created on {}".format(datetime.now().strftime("%c")),
                    "cidrRanges": [ip],
                    "scopes": [self.key_scopes],
                }

                LOG.info("Creating key with data %s.", str(data))

                resp = await session.post("https://developer.clashofclans.com/api/apikey/create", json=data)
                key = await resp.json()
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

        await session.close()
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

"""
MIT License

Copyright (c) 2019 mathsman5133

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
import time
import inspect
import logging
import re

from functools import wraps
from collections import OrderedDict, namedtuple

from coc.utils import custom_isinstance, find


LOG = logging.getLogger(__name__)

TAG_VALIDATOR = re.compile(r"(?P<tag>^\s*#?[PYLQGRJCUV0289]+\s*$)|(?P<location>\d{1,10})")
TAG_NAMES = {"location", "tag"}

CacheConfig = namedtuple("CacheConfig", ("max_size", "ttl"))  # a named tuple used with cache config.


def validate_tag(string):
    """Ensures the tag contains only valid characters.

    Legal clan tags only have these characters:
    Numbers: 0, 2, 8, 9
    Letters: P, Y, L, Q, G, R, J, C, U, V
    """
    if not isinstance(string, str):
        return False

    match = TAG_VALIDATOR.match(string)

    if match:
        if TAG_NAMES.intersection(match.groups()):
            return True

    return False


def find_key(args, kwargs):
    """Finds a tag-key from given args and kwargs."""
    if args:
        if find(validate_tag, args):
            return args

    for value in kwargs.values():
        if validate_tag(value):
            return value

    return None


class MaxSizeCache(OrderedDict):
    """Implements a basic Cache type which has a defined max size.

    This can be used with :class:`Cache` and should be created in the :meth`Cache.create_default_cache`.

    Once the cache has reached a set max size, it will eject the least recently used object.
    """

    __slots__ = ("max_size",)

    def __init__(self, max_size):
        self.max_size = max_size
        super().__init__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.check_max_size()

    def check_max_size(self):
        """Evicts the last used object if the max size has been surpassed."""
        if not self.max_size:
            return

        while len(self) > self.max_size:
            oldest = next(iter(self))
            LOG.debug(
                "Removed item with key %s from cache due to max size %s reached", oldest, self.max_size,
            )
            del self[oldest]


class TimeToLiveCache(OrderedDict):
    """Implements a basic Cache type which has a defined expiry/time to live.

    This can be used with :class:`Cache` and should be created in the :meth`Cache.create_default_cache`.

    Each object will be set with a timestamp, and upon retrieval,
    the cache will check to ensure the object has not surpassed the given expiry.
    If it has, it will eject the item from the cache and return ``None``.
    """

    __slots__ = ("ttl",)

    def __init__(self, ttl):
        self.ttl = ttl
        super().__init__()

    def __getitem__(self, key):
        self.check_expiry()

        value = super().__getitem__(key)

        try:
            self.move_to_end(key)
        except KeyError:
            pass

        return value[1]

    def __setitem__(self, key, value):
        super().__setitem__(key, (time.monotonic(), value))

    def values(self):
        """Remove injected timestamps from value results."""
        return [n[1] for n in super().values()]

    def check_expiry(self):
        """Evicts any objects which have surpassed maximum expiry."""
        if not self.ttl:
            return

        current_time = time.monotonic()
        to_delete = (k for k, (t, v) in tuple(self.items()) if current_time > t + self.ttl)
        for k in to_delete:
            LOG.debug("Removed item with key %s and TTL %s seconds from cache.", k, self.ttl)
            del self[k]


class DefaultCache(OrderedDict):
    """Implements the default Cache Type used within the library.

    This class inherits from `collections.OrderedDict` and
    implements a mix of a max-size LRU and expiry TTL cache.

    When the cache exceeds a given maximum size, it will eject objects least recently used.

    All items have a timestamp attached to them upon setting,
    and upon retrieval this is compared to ensure it does not exceed the expiry limit.
    If it does, the object will be disgarded and ``None`` returned."""

    __slots__ = ("max_size", "ttl")

    def __init__(self, max_size, ttl):
        self.max_size = max_size
        self.ttl = ttl
        super().__init__()

    def __getitem__(self, key):
        self.check_expiry()

        value = super().__getitem__(key)

        try:
            self.move_to_end(key)
        except KeyError:
            pass

        return value[1]

    def __setitem__(self, key, value):
        super().__setitem__(key, (time.monotonic(), value))
        self.check_expiry()
        self.check_max_size()

    def values(self):
        """Remove injected timestamps from value results."""
        return [n[1] for n in super().values()]

    def check_expiry(self):
        """Evicts any objects which have surpassed maximum expiry."""
        if not self.ttl:
            return

        current_time = time.monotonic()
        to_delete = (k for k, (t, v) in tuple(self.items()) if current_time > t + self.ttl)
        for k in to_delete:
            LOG.debug("Removed item with key %s and TTL %s seconds from cache.", k, self.ttl)
            del self[k]

    def check_max_size(self):
        """Evicts the last used object if the max size has been surpassed."""
        if not self.max_size:
            return

        while len(self) > self.max_size:
            oldest = next(iter(self))
            LOG.debug(
                "Removed item with key %s from cache due to max size %s reached", oldest, self.max_size,
            )
            del self[oldest]


class Cache:
    """The base Cache class for the library.

    The library's cache system works perfectly fine out-of-the box,
    and this class is purely for the purposes of creating a custom cache,
    if the library does not provide the functionality you require.

    Some examples of implementation of this cache are:

        1. Compatibility with an async-cache, for example aioredis
        2. Compatibility with a C-binding or other cache which has performance improvements
        3. Additional logging, debugging and other things you wish to do when creating,
           getting and setting items to the cache
        4. Using a database for the cache (not recommended for regular use)

    While all methods can be overridden, only the documented ones will be supported.
    What this means is that if something breaks because you override other methods, you're on your own.

    By default, the cache-type implemented mixes a LRU (least-recently used) and TTL (time to live) cache.
    This is a custom class, :class:`DefaultCache`, that checks both these properties before returning an object.

    Other classes, :class:`MaxSizeCache` and :class:`TimeToLiveCache` are
    provided for easy of use with :meth:`Cache.create_default_cache`.

    Attributes
    -------------
    client : coc.Client
        The coc.py client that created this cache instance.
    """

    def __init__(self, client):
        self.client = client

    @property
    def _cache_categories(self):
        """Groups cache types into categories."""
        return {
            "search_clans": "clan",
            "war_logs": "clan",
            "clan_wars": "war",
            "current_wars": "war",
            "league_groups": "war",
            "league_wars": "war",
            "war_clans": "war",
            "war_players": "war",
            "search_players": "player",
            "locations": "static",
            "leagues": "static",
            "seasons": "static",
            "events": "static",
        }

    @property
    def clan_config(self):
        """Override the default max size and expiry of the clan caches.

        This must return a named tuple, `coc.ClashConfig` with `max_size` and `ttl` attributes.

        By default, the cache uses a max size of 1024 and TTL of 3600 (1 hour).
        """
        return CacheConfig(1024, 3600)

    @property
    def player_config(self):
        """Override the default max size and expiry of the player caches.

        This must return a named tuple, `coc.ClashConfig` with `max_size` and `ttl` attributes.

        By default, the cache uses a max size of 1024 and TTL of 3600 (1 hour).
        """

        return CacheConfig(1024, 3600)

    @property
    def war_config(self):
        """Override the default max size and expiry of the war group of caches.

        This must return a named tuple, `coc.ClashConfig` with `max_size` and `ttl` attributes.

        By default, the cache uses a max size of 1024 and TTL of 3600 (1 hour).
        """

        return CacheConfig(1024, 1800)

    @property
    def static_config(self):
        """Override the default max size and expiry of the static group of caches.

        This must return a named tuple, `coc.ClashConfig` with `max_size` and `ttl` attributes.

        By default, the cache uses a max size of 1024 and TTL of 3600 (1 hour).
        """

        return CacheConfig(1024, None)

    @property
    def _config_by_group(self):
        """Maps cache categories to respective config settings."""
        return {
            "clan": self.clan_config,
            "player": self.player_config,
            "war": self.war_config,
            "static": self.static_config,
        }

    @staticmethod
    def create_default_cache(max_size, ttl):
        """This method creates and returns a cache instance.

        It takes the parameters `max_size` and `ttl`,
        and should return an appropriate instance of a cache object that reflects these parameters.

        This should be where you reference your "other" cache type, instance, object etc.
        """
        return DefaultCache(max_size=max_size, ttl=ttl)

    def get_max_size(self, cache_name):
        """Finds the custom max-size for a cache name."""
        category = self._cache_categories[cache_name]
        config = self._config_by_group[category]
        return config.max_size

    def get_ttl(self, cache_name):
        """Finds the custom expiry for a cache name."""
        category = self._cache_categories[cache_name]
        config = self._config_by_group[category]
        return config.ttl

    def register_cache_types(self):
        """Reset the cache types according to max-size and expiry values set.

        These can be set in :attr:`Cache.clan_config`, :attr:`Cache.player_config`, :attr:`Cache.war_config` and
        :attr:`Cache.static_config`.
        """
        for name in self._cache_categories:
            cache = self.create_default_cache(max_size=self.get_max_size(name), ttl=self.get_ttl(name))
            setattr(self, name, cache)

    def get_cache(self, cache_name):
        """Retrieve the cache instance for a cache name."""
        return getattr(self, cache_name)

    def reset_event_cache(self, cache_name: str):
        """Register cache types seperately for the :class:`EventsClient`.

        They cannot have a TTL otherwise events may be missed.
        Ideally the :func:`Cache.get_max_size` should return ``None``, however this may cause memory bloats.
        """
        cache = self.create_default_cache(max_size=self.get_max_size(cache_name), ttl=None)
        setattr(self, cache_name, cache)

    async def get(self, cache_type, key):
        """|coro|

        This method is used to get an item from a cache instance.

        By default, it gets the cache instance, set as an attribute of :class:`Cache` with the same name,
        then tries to use `__getitem__` on the cache instance. If that fails, it will try and
        get the object via the `cache.get` call.

        If your cache **does not** either implement `__getitem__` or the `.get(key)` methods,
        you **must** override this with the alternate approach to getting items from your cache.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** return the object in the cache with the given key.
        """
        cache = self.get_cache(cache_type)
        try:
            value = cache[key]
        except (KeyError, IndexError):
            get = cache.get
            if inspect.isawaitable(get):
                value = await get(key)
            else:
                value = get(key)

        return value

    async def set(self, cache_type, key, value):
        """|coro|

        This method is used to add a key/value pair to a cache instance.

        By default, it gets the cache instance, set as an attribute of :class:`Cache` with the same name,
        then tries to use `__setitem__` on the cache instance. If that fails, it will try and
        set the object via the `cache.set` call.

        If your cache **does not** either implement `__setitem__` or the `.set(key)` methods,
        you **must** override this with the alternate approach to setting items to your cache.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** set the key/value pair in the cache.
        Nothing is required to be returned.
        """
        cache = self.get_cache(cache_type)
        try:
            cache[key] = value
        except (KeyError, IndexError):
            setter = cache.set
            if inspect.isawaitable(setter):
                await setter(key, value)
            else:
                setter(key, value)

    async def pop(self, cache_type, key):
        """|coro|

        This method is used to get an item from a cache instance, deleting it at the same time.

        By default, it gets the cache instance, set as an attribute of :class:`Cache` with the same name,
        then tries to use `__getitem__` on the cache instance to get the item, then `del` call to remove it.
        If that fails, it will try and get the object and delete it at the same time via the `cache.pop` call.

        If your cache **does not** either implement `__getitem__` and `del`, or the `.pop(key)` methods,
        you **must** override this with the alternate approach to popping items from your cache.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** return a value with the given key.
        """
        cache = self.get_cache(cache_type)
        try:
            value = cache[key]
            del cache[key]
        except (KeyError, IndexError):
            pop = cache.pop
            if inspect.isawaitable(pop):
                value = await pop(key)
            else:
                value = pop(key)
        return value

    async def keys(self, cache_type):
        """|coro|

        This method is used to get all keys from a cache instance.

        By default, this implements the `cache.keys()` function.
        If your cache instance does not implement this method, you **must** override this method.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** return a list of strings; the keys of the cache.
        """
        cache = self.get_cache(cache_type)
        return cache.keys()

    async def values(self, cache_type):
        """|coro|

        This method is used to get all values from a cache instance.

        By default, this implements the `cache.values()` function.
        If your cache instance does not implement this method, you **must** override this method.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** return a list of objects; the values of the cache.
        """
        return self.get_cache(cache_type).values()

    async def items(self, cache_type):
        """|coro|

        This method is used to get all items from a cache instance.

        By default, this implements the `cache.items()` function.
        If your cache instance does not implement this method, you **must** override this method.

        As this function is a coroutine, you **can** `await` calls.

        This function **must** return a list of {k, v} values: the items of the cache.
        """
        return self.get_cache(cache_type).items()

    async def clear(self, cache_type):
        """|coro|

        This method is used to remove all items from the cache instance.

        By default, this implements the `cache.clear()` function.
        If your cache instance does not implement this method, you **must** override this method.

        As this function is a coroutine, you **can** `await` calls.

        This function does not need to return anything.
        """
        return self.get_cache(cache_type).clear()

    async def get_limit(self, cache_type, limit: int = None):
        """Custom implementation of the `limits()` function to properly return values without timestamps."""
        call = await self.values(cache_type)
        if not limit:
            return call
        return call[:limit]


def events_cache():
    """Adds all events dispatched to seperate cache for use with :ref:`working_with_batch_updates`."""

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            class_instance = args[0]  # self will always be first arg
            cache = class_instance.cache
            if not cache:
                return func(*args, **kwargs)

            event_name = args[1]
            if event_name.endswith("batch_updates"):
                return func(*args, **kwargs)

            event_args = list(args[1:])
            event_args.extend(kwargs.values())

            key = f"{event_name}.{time.monotonic()}"
            asyncio.ensure_future(cache.set("events", key, event_args))

            return func(*args, **kwargs)

        return wrapper

    return deco


def cached(cache_name):
    """
    Helper for registering return values of functions to the cache, and retrieving from the cache if a key is found.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            class_instance = args[0]  # self will always be first arg
            cache = class_instance.cache
            if not cache:
                return await func(*args, **kwargs)  # the client doesn't have a cache registered. ignore.

            key = find_key(args, kwargs)
            use_cache = kwargs.pop("cache", False)
            fetch = kwargs.pop("fetch", True)
            update_cache = kwargs.pop("update_cache", True)

            if custom_isinstance(class_instance, __name__, "EventsClient"):  # workaround to stop recursion imports.
                update_cache = False  # we never want to automatically update cache for EventsClient.

            # todo: clean this up
            if not key:
                return await func(*args, **kwargs)

            if use_cache:
                try:
                    data = await cache.get(cache_name, key)
                except KeyError:
                    data = None
            else:
                if fetch:
                    data = await func(*args, **kwargs)
                    if update_cache:
                        await cache.set(cache_name, key, data)
                else:
                    data = None

            if not data:
                if fetch:
                    data = await func(*args, **kwargs)
                if update_cache:
                    await cache.set(cache_name, key, data)
                return data

            LOG.debug("Using cached object with KEY: %s and VALUE: %s", key, data)
            return data

        return wrapper

    return decorator

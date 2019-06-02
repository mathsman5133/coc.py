import time
import inspect
import logging
import re

from functools import wraps
from collections import OrderedDict

from coc.utils import find


log = logging.getLogger(__name__)


def validate_tag(string):
    # Legal clan tags only have these characters:
    # Numbers: 0, 2, 8, 9
    # Letters: P, Y, L, Q, G, R, J, C, U, V
    if not isinstance(string, str):
        return False

    match = re.match("(?P<tag>^\s*#?[PYLQGRJCUV0289]+\s*$)|(?P<location>\d{1,10})", string)

    if not match:
        return False
    if match.group('tag'):
        return True
    if match.group('location'):
        return True

    return False


def find_key(args, kwargs):
    if args:
        key = find(lambda x: validate_tag(x), args)
        if key:
            return key

    for k, v in kwargs.items():
        key = validate_tag(v)
        if key:
            return v

    return None


def _wrap_coroutine(result):
    async def new_coro():
        return result
    return new_coro()


def _wrap_store_coro(cache, key, coro, update_cache):
    async def fctn():
        value = await coro
        if update_cache:
            cache[key] = value

        return value
    return fctn()


def _try_wrap_store_coro(cache, key, data, update_cache):
    if inspect.isawaitable(data):
        return _wrap_store_coro(cache, key, data, update_cache)
    if inspect.isasyncgen(data):
        return data

    if update_cache:
        cache[key] = data

    return data


class LRU(OrderedDict):
    __slots__ = ('max_size', 'ttl')

    def __init__(self, max_size, ttl):
        self.max_size = max_size
        self.ttl = ttl
        super().__init__()

    def __getitem__(self, key):
        self.check_expiry()

        value = super().__getitem__(key)
        self.move_to_end(key)
        return value[1]

    def __setitem__(self, key, value):
        super().__setitem__(key, (time.monotonic(), value))
        self.check_expiry()
        self.check_max_size()

    def check_expiry(self):
        if not self.ttl:
            return

        current_time = time.monotonic()
        to_delete = [k for (k, (t, v)) in self.items() if current_time > (t + self.ttl)]
        for k in to_delete:
            log.debug('Removed item with key %s and TTL %s seconds from cache.', k, self.ttl)
            del self[k]

    def check_max_size(self):
        if not self.max_size:
            return

        while len(self) > self.max_size:
            oldest = next(iter(self))
            log.debug('Removed item with key %s from cache due to max size %s reached', oldest, self.max_size)
            del self[oldest]


class Cache:
    __slots__ = ('cache', 'ttl', 'max_size', 'fully_populated',
                 '_is_clan', '_is_player', '_is_war', '_is_static')

    def __init__(self, max_size=128, ttl=None):
        self.cache = LRU(max_size, ttl)
        self.ttl = self.cache.ttl
        self.max_size = self.cache.max_size
        self.fully_populated = False

        self._is_clan = False
        self._is_player = False
        self._is_war = False
        self._is_static = False

    def __call__(self, *args, **kwargs):
        self.cache.check_expiry()

    def get_cache(self):
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = find_key(args, kwargs)
                cache = kwargs.pop('cache', False)
                fetch = kwargs.pop('fetch', True)
                update_cache = kwargs.pop('update_cache', True)

                if not key:
                    return func(*args, **kwargs)

                if cache:
                    data = self.get(key)
                else:
                    if fetch:
                        data = func(*args, **kwargs)
                        return _try_wrap_store_coro(self.cache, key, data, update_cache)

                    else:
                        return None

                if not data:
                    if fetch:
                        data = func(*args, **kwargs)
                    else:
                        return None

                    return _try_wrap_store_coro(self.cache, key, data, update_cache)

                else:
                    log.debug('Using cached object with KEY: %s and VALUE: %s', key, data)
                    if inspect.iscoroutinefunction(func):
                        return _wrap_coroutine(data)

                    return data

            return wrapper
        return deco

    def get(self, key):
        self.cache.check_expiry()
        try:
            return self.cache[key]
        except KeyError:
            return None

    def add(self, key, value):
        self.cache[key] = value

    def clear(self, max_size=None, ttl=None):
        if not max_size:
            max_size = self.max_size
        if not ttl:
            ttl = self.ttl

        self.cache = LRU(max_size, ttl)

    def get_all_values(self):
        self.cache.check_expiry()
        return list(n[1] for n in self.cache.values())

    def get_limit(self, limit: int=None):
        self.cache.check_expiry()
        if not limit:
            return self.get_all_values()

        return self.get_all_values()[:limit]

    def events_cache(self):
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                event_name = args[1]
                if event_name.endswith('batch_updates'):
                    return func(*args, **kwargs)

                event_args = [n for n in args[1:]].extend(kwargs.values())

                key = f'{event_name}.{time.monotonic()}'

                self.add(key, event_args)

                return func(*args, **kwargs)
            return wrapper
        return deco
                



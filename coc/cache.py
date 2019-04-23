from lru import LRU
from functools import wraps
import time
from coc.utils import find
import inspect
import logging
import re

log = logging.getLogger(__name__)


def validate_tag(tag):
    # Legal clan tags only have these characters:
    # Numbers: 0, 2, 8, 9
    # Letters: P, Y, L, Q, G, R, J, C, U, V
    if not isinstance(tag, str):
        return False
    match = re.match("^#[PYLQGRJCUV0289]+$", tag)
    return True if match else False


def find_key(args, kwargs):
    if args:
        key = find(lambda x: validate_tag(x), args)
        if key:
            return key

    for k, v in kwargs.items():
        key = validate_tag(v)
        if key:
            return key

    return None


def _wrap_coroutine(result):
    async def new_coro():
        return result[0]
    return new_coro()


def _wrap_store_coro(cache, key, coro):
    async def fctn():
        value = await coro
        cache[key] = (value, time.monotonic())
        return value
    return fctn()


class Cache:
    def __init__(self, max_size=128, ttl=None):
        self.__lru_instance = LRU(max_size)
        self.__ttl = ttl

    def __call__(self, *args, **kwargs):
        self.check_expiry()

    def check_expiry(self):
        if not self.__ttl:
            return

        current_time = time.monotonic()
        to_delete = [k for (k, (v, t)) in self.__lru_instance.items() if current_time > (t + self.__ttl)]
        for k in to_delete:
            log.debug('Removed item with key %s and TTL %s seconds from cache.', k, self.__ttl)
            del self.__lru_instance[k]

    def get_cache(self):
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.check_expiry()
                key = find_key(args, kwargs)
                cache = kwargs.pop('cache', False)
                fetch = kwargs.pop('fetch', True)

                if not key:
                    return func(*args, **kwargs)
                try:
                    if cache:
                        data = self.__lru_instance[key]
                    else:
                        if fetch:
                            data = func(*args, **kwargs)
                            return _wrap_store_coro(self.__lru_instance,
                                                    key, data)
                        else:
                            return None

                except KeyError:
                    if fetch:
                        data = func(*args, **kwargs)
                    else:
                        return None

                    if inspect.isasyncgen(data):
                        return data

                    if inspect.isawaitable(data):
                        return _wrap_store_coro(self.__lru_instance,
                                                key, data)

                    self.__lru_instance[key] = (data, time.monotonic())
                    return data

                else:
                    log.debug('Using object cached at %s', data[1])
                    if inspect.iscoroutinefunction(func):
                        return _wrap_coroutine(data)

                    return data

            return wrapper
        return deco

    def get(self, key):
        try:
            return self.__lru_instance[key]
        except KeyError:
            return None

    def add(self, key, value):
        self.__lru_instance[key] = (value, time.monotonic())


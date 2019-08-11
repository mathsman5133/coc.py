import time
import inspect
import logging
import re

from functools import wraps
from collections import OrderedDict, namedtuple

from coc.utils import find


log = logging.getLogger(__name__)

tag_validator = re.compile("(?P<tag>^\s*#?[PYLQGRJCUV0289]+\s*$)|(?P<location>\d{1,10})")
tag_names = {'location', 'tag'}

CacheConfig = namedtuple('CacheConfig', ('max_size', 'ttl'))


def validate_tag(string):
    # Legal clan tags only have these characters:
    # Numbers: 0, 2, 8, 9
    # Letters: P, Y, L, Q, G, R, J, C, U, V
    if not isinstance(string, str):
        return False

    match = tag_validator.match(string)

    if match:
        if tag_names.intersection(match.groups()):
            return True

    return False


def find_key(args, kwargs):
    if args:
        if find(validate_tag, args):
            return args

    for v in kwargs.values():
        if validate_tag(v):
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


class MaxSizeCache(OrderedDict):
    __slots__ = 'max_size'

    def __init__(self, max_size):
        self.max_size = max_size
        super().__init__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.check_max_size()

    def check_max_size(self):
        if not self.max_size:
            return

        while len(self) > self.max_size:
            oldest = next(iter(self))
            log.debug('Removed item with key %s from cache due to max size %s reached', oldest,
                      self.max_size
                      )
            del self[oldest]


class TimeToLiveCache(OrderedDict):
    __slots__ = 'ttl'

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
        return [n[1] for n in super().values()]

    def check_expiry(self):
        if not self.ttl:
            return

        current_time = time.monotonic()
        to_delete = (k for k, (t, v) in tuple(self.items()) if current_time > t + self.ttl)
        for k in to_delete:
            log.debug('Removed item with key %s and TTL %s seconds from cache.', k, self.ttl)
            del self[k]


class DefaultCache(OrderedDict):
    __slots__ = ('max_size', 'ttl')

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
        return [n[1] for n in super().values()]

    def check_expiry(self):
        if not self.ttl:
            return

        current_time = time.monotonic()
        to_delete = (k for k, (t, v) in tuple(self.items()) if current_time > t + self.ttl)
        for k in to_delete:
            log.debug('Removed item with key %s and TTL %s seconds from cache.', k, self.ttl)
            del self[k]

    def check_max_size(self):
        if not self.max_size:
            return

        while len(self) > self.max_size:
            oldest = next(iter(self))
            log.debug('Removed item with key %s from cache due to max size %s reached', oldest,
                      self.max_size
                      )
            del self[oldest]

    def get_limit(self, limit: int = None):
        if not limit:
            return self.values()

        return self.values()[:limit]


class Cache:
    def __init__(self, client):
        self.client = client

    @property
    def cache_categories(self):
        return {
            'search_clans': 'clan',
            'war_logs': 'clan',

            'clan_wars': 'war',
            'current_wars': 'war',
            'league_groups': 'war',
            'league_wars': 'war',
            'war_clans': 'war',
            'war_players': 'war',

            'search_players': 'player',

            'locations': 'static',
            'leagues': 'static',
            'seasons': 'static',

            'events': 'static'
        }

    @property
    def clan_config(self):
        return CacheConfig(1024, 3600)

    @property
    def player_config(self):
        return CacheConfig(1024, 3600)

    @property
    def war_config(self):
        return CacheConfig(1024, 1800)

    @property
    def static_config(self):
        return CacheConfig(1024, None)

    @property
    def config_by_group(self):
        return {
            'clan': self.clan_config,
            'player': self.player_config,
            'war_config': self.war_config,
            'static_config': self.static_config
        }

    @staticmethod
    def create_default_cache(max_size, ttl):
        return DefaultCache(max_size=max_size, ttl=ttl)

    def get_max_size(self, cache_name):
        category = self.cache_categories[cache_name]
        config = self.config_by_group[category]
        return config.max_size

    def get_ttl(self, cache_name):
        category = self.cache_categories[cache_name]
        config = self.config_by_group[category]
        return config.ttl

    def register_cache_types(self):
        for name in self.cache_categories.keys():
            cache = self.create_default_cache(
                max_size=self.get_max_size(name),
                ttl=self.get_ttl(name)
            )
            setattr(self, name, cache)

    def get_cache(self, cache_name):
        return getattr(self, cache_name)

    def reset_event_cache(self, cache_name: str):
        cache = self.create_default_cache(
            max_size=self.get_max_size(cache_name),
            ttl=None
        )
        setattr(self, cache_name, cache)


def events_cache():
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            class_instance = args[0]  # self will always be first arg
            cache = class_instance.cache.get_cache('events')

            event_name = args[1]
            if event_name.endswith('batch_updates'):
                return func(*args, **kwargs)

            event_args = [n for n in args[1:]]
            event_args.extend(kwargs.values())

            key = f'{event_name}.{time.monotonic()}'

            cache[key] = event_args

            return func(*args, **kwargs)
        return wrapper
    return deco


def cached(cache_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            class_instance = args[0]  # self will always be first arg
            cache = class_instance.cache.get_cache(cache_name)

            key = find_key(args, kwargs)
            use_cache = kwargs.pop('cache', False)
            fetch = kwargs.pop('fetch', True)
            update_cache = kwargs.pop('update_cache', True)

            if not key:
                return func(*args, **kwargs)

            if use_cache:
                try:
                    data = cache[key]
                except KeyError:
                    data = None
            else:
                if fetch:
                    data = func(*args, **kwargs)
                    return _try_wrap_store_coro(cache, key, data, update_cache)

                else:
                    return None

            if not data:
                if fetch:
                    data = func(*args, **kwargs)
                else:
                    return None

                return _try_wrap_store_coro(cache, key, data, update_cache)

            else:
                log.debug('Using cached object with KEY: %s and VALUE: %s', key, data)
                if inspect.iscoroutinefunction(func):
                    return _wrap_coroutine(data)

                return data

        return wrapper
    return decorator


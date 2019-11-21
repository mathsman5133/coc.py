.. currentmodule:: coc

Custom Cache
==============
The following section outlines the custom cache capabilities of the library,
providing a basic guide on best practices and a simple how-to.

The Default Cache
-------------------
By default, coc.py uses an OrderedDict as the cache class.

However, it modifies this by adding in a max size and expiry time for objects.
Upon entering the cache, all objects are given a timestamp, and if the distance
between retrieval time and when the object was put in the cache is greater than a
defined amount, the object is disgarded and None is returned. Similarly, if the
cache exceeds the maximum size, the least recently used object is disgarded.

This is a simple, lightweight and effective method of caching.
For the average user, it is more than adequete.

Modifying Max Size and Time To Live
-----------------------------------
One of the options for modifying the cache is to change the settings for max size
and time to live, on a 'per group' basis. The groups are as follows:


The Default Max Size/Time To Live for each group are detailed below:

+-------------+----------+--------------------------+
| Cache Group | Max Size | Time To Live             |
+-------------+----------+--------------------------+
| ``clan``    | ``1024`` | ``3600 sec (1hour)``     |
+-------------+----------+--------------------------+
| ``war``     | ``1024`` | ``1800 sec (0.5 hr)``    |
+-------------+----------+--------------------------+
| ``player``  | ``1024`` | ``3600 sec (1hour)``     |
+-------------+----------+--------------------------+
| ``static``  | ``1024`` | ``None (never expires)`` |
+-------------+----------+--------------------------+

Where each of the groups correspond to the following cached objects:

+-----------------------+---------------+
|     Cache Name        |    Group      |
+-----------------------+---------------+
| ``Search clans``      | ``clan``      |
+-----------------------+---------------+
| ``Clan War Logs``     | ``clan``      |
+-----------------------+---------------+
| ``Clan Wars``         | ``war``       |
+-----------------------+---------------+
| ``Current Wars``      | ``war``       |
+-----------------------+---------------+
| ``War League Groups`` | ``war``       |
+-----------------------+---------------+
| ``League Wars``       | ``war``       |
+-----------------------+---------------+
| ``War Clans``         | ``war``       |
+-----------------------+---------------+
| ``War Players``       | ``war``       |
+-----------------------+---------------+
| ``Search Players``    | ``player``    |
+-----------------------+---------------+
| ``Locations``         | ``static``    |
+-----------------------+---------------+
| ``Leagues``           | ``static``    |
+-----------------------+---------------+
| ``Seasons``           | ``static``    |
+-----------------------+---------------+
| ``Events Run``        | ``static``    |
+-----------------------+---------------+



These default max size and time to live can be overidden like follows:

.. code-block:: python3

    import coc

    class CustomCache(coc.Cache):
        @property
        def clan_config(self):
            return coc.CacheConfig(128, 60)  # max_size, time to live

        @property
        def player_config(self):
            return coc.CacheConfig(256, 30)  # max size = 256, time to live = 30

Where ``coc.CacheConfig`` is a named tuple where max size and time to live can be set.

You would then pass this custom cache class into your ``coc.login`` function.

.. code-block:: python3

    import coc

    client = coc.login('email', 'password', cache=CustomCache)

Where ``CustomCache`` is your custom cache class.

Modifying the Default Cache Instance Type
------------------------------------------
Sometimes you may wish to change the type of cache instance completely.
The default cache instance/class is an OrderedDict - an inbuilt dict from the `collections` module.

The library does, however, provide support for different classes than regular dicts.
This provides the user with the opportunity to use an async compatabile cache, redis (or aioredis),
through to an in-memory database (sqlite3 is one).

When customising the cache instance, a few important things should be noted:

    1. By default, the library tries to index the cache object with a key, ie ``cache[key]`` to get a value.
       If this fails, it will fallback to a .get(key) method of the cache, which can be a coroutine. If your
       cache instance does not support either operation, you **must** override the ``cache.get()`` method.
       More can be found in :meth:`Cache.get`

    2. The same applies for ``cache.set(key, value)``, ``cache.pop(key)``, ``cache.items()``, ``cache.values()``,
       ``cache.keys()`` and ``cache.clear()``. All of these methods are coroutines.

    3. If applicable, checking for maximum size and TTL of objects should be done in this class instance.
       The library does not handle TTL outside of the default cache classes.

A few examples:

.. code-block:: python3

    # to use a cache with only a max size; no TTL.

    from coc import MaxSizeCache, Cache, login

    class CustomCache(Cache):
        def create_default_cache(self, max_size, ttl):
            return MaxSizeCache(max_size)

    client = login('email', 'password', cache=CustomCache)

.. code-block:: python3

    # simarly, to use a cache with only TTL; no max size:

    from coc import TimeToLiveCache, Cache, login

    class CustomCache(Cache):
        def create_default_cache(self, max_size, ttl):
            return TimeToLiveCache(ttl)

    client = login('email', 'password', cache=CustomCache)

.. code-block:: python3

    # using aioredis as cache

    import aioredis
    from coc import Cache, EventsClient, login

    class CustomCache(Cache):
        def create_default_cache(self, name, max_size, ttl):
            return

        def make_key(cache_type, key):
            return f'{cache_type}:{key}'

        async def get(cache_type, key):
            new_key = self.make_key(cache_type, key)
            return await self.client.redis.get(new_key)

        async def set(cache_type, key, value):
            new_key = self.make_key(cache_type, key)
            expiry = self.get_ttl(cache_type)
            await self.client.redis.set(new_key, value, expire=expiry)

        async def pop(cache_type, key):
            new_key = self.make_key(cache_type, key)
            return await self.client.redis.lpop(new_key)

        async def keys(cache_type, limit=0):
            cur, keys = await self.client.redis.scan(match=cache_type, count=limit)
            return keys

        async def values(cache_type):
            keys = await self.keys(cache_type)
            return (await self.client.redis.get(k) for k in keys)

        async def items(cache_type):
            keys = await self.keys(cache_type)
            return ((k, await self.client.redis.get(k)) for k in keys)

        async def clear(self, cache_type):
            await self.client.redis.flushdb()

        async def get_limit(self, cache_type, limit):
            keys = await self.keys(cache_type, limit=limit)
            return ((k, await self.client.redis.get(k)) for k in keys


    class CustomClient(EventsClient):
        def __init__(self, **options):
            super().__init__(**options)
            self.redis = aioredis.create_redis('redis://localhost')

        async def on_client_close(self):
            self.redis.close()
            await self.redis.wait_closed()


    client = coc.login('email', 'password', client=CustomClient, cache=CustomCache)

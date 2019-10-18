import asyncio

from collections import Iterable

from .errors import NotFound, Forbidden
from .utils import item


class _AsyncIterator:
    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            msg = await self.next()
        except StopAsyncIteration:
            raise StopAsyncIteration()
        else:
            return msg

    async def flatten(self):
        ret = []
        while True:
            try:
                msg = await self.next()
            except StopAsyncIteration:
                return ret
            else:
                ret.append(msg)


class TaggedIterator(_AsyncIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **kwargs):
        self.client = client
        self.tags = tags

        self.cache = cache
        self.fetch = fetch
        self.update_cache = update_cache
        self.queue = asyncio.Queue(loop=client.loop)
        self.queue_empty = True

        self.iter_options = kwargs

    async def run_method(self, tag: str):
        try:
            return await self.get_method(tag, cache=self.cache, fetch=self.fetch, update_cache=self.update_cache)
        except (NotFound, Forbidden):
            return None

    async def fill_queue(self):
        tasks = [
            asyncio.ensure_future(
                self.run_method(
                    item(n, **self.iter_options)
                )
            )
            for n in self.tags
        ]

        result = await asyncio.gather(*tasks)

        for n in result:
            if n:
                await self.queue.put(n)

    async def next(self):
        if self.queue_empty:
            try:
                await self.fill_queue()
            except KeyError:
                await self.client.reset_keys()
                return await self.next()
            
            self.queue_empty = False

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration


class ClanIterator(TaggedIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        super(ClanIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_clan


class PlayerIterator(TaggedIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        super(PlayerIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_player


class ClanWarIterator(TaggedIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        super(ClanWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_clan_war


class LeagueWarIterator(TaggedIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        super(LeagueWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_league_war


class CurrentWarIterator(TaggedIterator):
    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        super(CurrentWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_current_war

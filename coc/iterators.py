import asyncio

from .errors import NotFound, Forbidden


class _AsyncIterator:
    async def __aiter__(self):
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
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        self.client = client
        self.tags = tags

        self.cache = cache
        self.fetch = fetch
        self.queue = asyncio.Queue(loop=client.loop)
        self.queue_empty = True

    async def run_method(self, tag):
        try:
            return await self.get_method(tag, cache=self.cache, fetch=self.fetch)
        except (NotFound, Forbidden):
            return None

    async def fill_queue(self):
        tasks = []

        for tag in self.tags:
            task = asyncio.ensure_future(self.run_method(tag))
            tasks.append(task)

        result = await asyncio.gather(*tasks)
        result = [n for n in result if n]

        for n in result:
            await self.queue.put(n)

    async def next(self):
        if self.queue_empty:
            await self.fill_queue()
            self.queue_empty = False

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration


class ClanIterator(TaggedIterator):
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        super(ClanIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_clan


class PlayerIterator(TaggedIterator):
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        super(PlayerIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_player


class WarIterator(TaggedIterator):
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        self.tags = tags
        super(WarIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_current_war

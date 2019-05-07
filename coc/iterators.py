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
        self.retrieved = 0

        self.cache = cache
        self.fetch = fetch

    async def next(self):
        index = self.retrieved
        if index > len(self.tags) - 1:
            raise StopAsyncIteration

        self.retrieved += 1

        tag = self.tags[index]
        clan = await self.get_method(tag, cache=self.cache, fetch=self.fetch)
        return clan


class ClanIterator(TaggedIterator):
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        super(ClanIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_clan


class PlayerIterator(TaggedIterator):
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        super(PlayerIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_player


class WarIterator:
    def __init__(self, client, tags: list, cache: bool, fetch: bool):
        super(WarIterator, self).__init__(client, tags, cache, fetch)
        self.get_method = client.get_current_war

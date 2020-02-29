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

from collections.abc import Iterable

from .errors import Maintenance, NotFound, Forbidden
from .utils import item


class _AsyncIterator:
    """Base class for all async iterators."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            msg = await self._next()
        except StopAsyncIteration:
            raise StopAsyncIteration()
        else:
            return msg

    async def flatten(self):
        """
        |coro|

        Flattens the async iterator into a :class:`list` with all the elements.

        Returns
        --------
        :class:`list` - A list of every element in the async iterator.
        """
        ret = []
        while True:
            try:
                msg = await self._next()
            except StopAsyncIteration:
                return ret
            else:
                ret.append(msg)

    async def _next(self):
        return


class TaggedIterator(_AsyncIterator):
    """Implements filling of the queue and fetching results."""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **kwargs):
        # pylint: disable=too-many-arguments
        self.client = client
        self.tags = tags

        self.cache = cache
        self.fetch = fetch
        self.update_cache = update_cache
        self.queue = asyncio.Queue(loop=client.loop)
        self.queue_empty = True

        self.iter_options = kwargs
        self.get_method = None  # set in subclass

    async def _run_method(self, tag: str):
        # pylint: disable=not-callable
        try:
            return await self.get_method(tag, cache=self.cache, fetch=self.fetch, update_cache=self.update_cache)
        except (NotFound, Forbidden, Maintenance):
            return None

    async def _fill_queue(self):
        tasks = [asyncio.ensure_future(self._run_method(item(n, **self.iter_options))) for n in self.tags]

        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                await self.queue.put(result)

    async def _next(self):
        """Retrieves the next item from the queue. If empty, fill the queue first."""
        if self.queue_empty:
            try:
                await self._fill_queue()
            except KeyError:
                await self.client.reset_keys()
                return await self._next()

            self.queue_empty = False

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration


class ClanIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_clans`"""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        # pylint: disable=too-many-arguments
        super(ClanIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_clan


class PlayerIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_players`"""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        # pylint: disable=too-many-arguments
        super(PlayerIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_player


class ClanWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_clan_wars`"""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        # pylint: disable=too-many-arguments
        super(ClanWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_clan_war


class LeagueWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_league_wars`"""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        # pylint: disable=too-many-arguments
        super(LeagueWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_league_war


class CurrentWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_current_wars`"""

    def __init__(self, client, tags: Iterable, cache: bool, fetch: bool, update_cache: bool, **iter_options):
        # pylint: disable=too-many-arguments
        super(CurrentWarIterator, self).__init__(client, tags, cache, fetch, update_cache, **iter_options)
        self.get_method = client.get_current_war

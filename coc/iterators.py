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

from collections.abc import Iterable

from .errors import Maintenance, NotFound, Forbidden


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

    def __init__(self, client, tags: Iterable, cls, **kwargs):
        # pylint: disable=too-many-arguments
        self.client = client
        self.tags = tags

        self.cls = cls
        self.kwargs = kwargs

        self.queue = asyncio.Queue()
        self.queue_empty = True

        self.get_method = None  # set in subclass

    async def _run_method(self, tag: str):
        # pylint: disable=not-callable
        try:
            # I'm yet to find a way to only pass an arg/kwarg if it's not None, so lets just do this in interim
            if self.cls:
                return await self.get_method(tag, cls=self.cls, **self.kwargs)
            return await self.get_method(tag, **self.kwargs)
        except (NotFound, Forbidden, Maintenance):
            return None

    async def _fill_queue(self):
        tasks = [self.client.loop.create_task(self._run_method(n)) for n in self.tags]

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

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_clan


class PlayerIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_players`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = self.get_player

        self.members = kwargs.pop("members", {})

    async def get_player(self, tag, cls=None, **kwargs):
        if cls:
            player = await self.client.get_player(tag, cls=cls, **kwargs)
        else:
            player = await self.client.get_player(tag, **kwargs)

        player._inject_clan_member(self.members.get(tag))
        return player


class ClanWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_clan_wars`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_clan_war


class LeagueWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_league_wars`"""

    def __init__(self, client, tags: Iterable, clan_tag=None, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, clan_tag=clan_tag, **kwargs)
        self.get_method = client.get_league_war
        self.clan_tag = clan_tag

    async def _next(self):
        war = await super()._next()
        if war is None:
            return None
        elif self.clan_tag is None:
            return war
        elif war.clan_tag != self.clan_tag:
            return await self._next()
        else:
            return war


class CurrentWarIterator(TaggedIterator):
    """Iterator for use with :meth:`~coc.Client.get_current_wars`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_current_war

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
import concurrent.futures
import queue

from collections.abc import Iterable

from .errors import Maintenance, NotFound, Forbidden


class _Iterator:
    """Implements filling of the queue and fetching results."""

    def __init__(self, client, tags: Iterable, cls, **kwargs):
        # pylint: disable=too-many-arguments
        self.client = client
        self.tags = tags

        self.cls = cls
        self.kwargs = kwargs

        self.queue = asyncio.Queue() if client.is_async() else queue.Queue()
        self.queue_empty = True

        self.get_method = None  # set in subclass

    def __aiter__(self):
        if not self.client.is_async():
            raise RuntimeError("You cannot use an async-for with the sync client.")

        return self

    async def __anext__(self):
        try:
            result = await self.async_next()
        except StopAsyncIteration:
            raise StopAsyncIteration()
        else:
            return result

    def __iter__(self):
        if self.client.is_async():
            raise RuntimeError("You cannot use an regular for with the async client.")

        return self

    def __next__(self):
        try:
            result = self.next()
        except StopIteration:
            raise StopIteration()
        else:
            return result

    def sync_flatten(self):
        ret = []
        while True:
            try:
                result = self.next()
            except StopIteration:
                return ret
            else:
                ret.append(result)

    async def async_flatten(self):
        ret = []
        while True:
            try:
                result = await self.async_next()
            except StopAsyncIteration:
                return ret
            else:
                ret.append(result)

    flatten = async_flatten

    def run_method(self, tag: str):
        try:
            if self.cls:
                return self.get_method(tag, cls=self.cls, **self.kwargs)
            return self.get_method(tag, cls=self.cls, **self.kwargs)
        except (NotFound, Forbidden, Maintenance):
            return None

    def fill_queue(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(self.run_method, tag) for tag in self.tags]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                except:
                    continue
                else:
                    if result:
                        self.queue.put(result)

    def next(self):
        """Retrieves the next item from the queue. If empty, fill the queue first."""
        if self.queue_empty:
            try:
                self.fill_queue()
            except KeyError:
                self.client.reset_keys()
                return self.next()

            self.queue_empty = False

        try:
            return self.queue.get_nowait()
        except queue.Empty:
            raise StopIteration

    async def async_run_method(self, tag: str):
        # pylint: disable=not-callable
        try:
            # I'm yet to find a way to only pass an arg/kwarg if it's not None, so lets just do this in interim
            if self.cls:
                return await self.get_method(tag, cls=self.cls, **self.kwargs)
            return await self.get_method(tag, **self.kwargs)
        except (NotFound, Forbidden, Maintenance):
            return None

    async def async_fill_queue(self):
        tasks = [self.client.loop.create_task(self.async_run_method(n)) for n in self.tags]

        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                await self.queue.put(result)

    async def async_next(self):
        """Retrieves the next item from the queue. If empty, fill the queue first."""
        if self.queue_empty:
            try:
                await self.async_fill_queue()
            except KeyError:
                await self.client.reset_keys()
                return await self.async_next()

            self.queue_empty = False

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration


class ClanIterator(_Iterator):
    """Iterator for use with :meth:`~coc.Client.get_clans`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_clan


class PlayerIterator(_Iterator):
    """Iterator for use with :meth:`~coc.Client.get_players`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_player


class ClanWarIterator(_Iterator):
    """Iterator for use with :meth:`~coc.Client.get_clan_wars`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_clan_war


class LeagueWarIterator(_Iterator):
    """Iterator for use with :meth:`~coc.Client.get_league_wars`"""

    def __init__(self, client, tags: Iterable, clan_tag=None, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, clan_tag=clan_tag, **kwargs)
        self.get_method = client.get_league_war
        self.clan_tag = clan_tag

    async def async_next(self):
        war = await self.async_next()
        if war is None:
            return None
        elif self.clan_tag is None:
            return war
        elif war.clan_tag != self.clan_tag:
            return await self.async_next()
        else:
            return war

    def next(self):
        war = self.next()
        if war is None:
            return None
        elif self.clan_tag is None:
            return war
        elif war.clan_tag != self.clan_tag:
            return self.next()
        else:
            return war


class CurrentWarIterator(_Iterator):
    """Iterator for use with :meth:`~coc.Client.get_current_wars`"""

    def __init__(self, client, tags: Iterable, cls=None, **kwargs):
        # pylint: disable=too-many-arguments
        super().__init__(client, tags, cls, **kwargs)
        self.get_method = client.get_current_war

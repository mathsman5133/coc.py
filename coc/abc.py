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
from typing import AsyncIterator, Type, TYPE_CHECKING

from .miscmodels import try_enum, Badge
from .iterators import PlayerIterator

if TYPE_CHECKING:
    from .players import Player


class BaseClan:
    """An ABC that implements some common operations on clans, regardless of type.

    Attributes
    ----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    """

    __slots__ = ("tag", "name", "_client", "badge", "level", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % (self.__class__.__name__, self.tag, self.name)

    def __eq__(self, other):
        return isinstance(other, BaseClan) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.badge = try_enum(Badge, data=data.get("badgeUrls"), client=self._client)
        self.level = data.get("clanLevel")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the clan in-game"""
        return "https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{}".format(self.tag.strip("#"))

    @property
    def members(self):
        # pylint: disable=missing-function-docstring
        return NotImplemented

    def get_detailed_members(self, cls: Type["Player"] = None) -> AsyncIterator["Player"]:
        """Get detailed player information for every player in the clan.

        This returns a :class:`PlayerIterator` which fetches all player tags in the clan in parallel.

        Example
        ---------

        .. code-block:: python3

            clan = await client.get_clan('tag')

            async for player in clan.get_detailed_members():
                print(player.name)


        Yields
        ------
        :class:`Player`
            A full player object of a clan member.
        """
        if self.members is NotImplemented:
            return NotImplemented

        return PlayerIterator(self._client, (p.tag for p in self.members), cls=cls)


class BasePlayer:
    """An ABC that implements some common operations on players, regardless of type.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    """

    __slots__ = ("tag", "name", "_client", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % (self.__class__.__name__, self.tag, self.name,)

    def __eq__(self, other):
        return isinstance(other, BasePlayer) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")

        self.tag = data.get("tag")
        self.name = data.get("name")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the player in-game"""
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))

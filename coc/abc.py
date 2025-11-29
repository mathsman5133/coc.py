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
from pathlib import Path
from typing import AsyncIterator, Type, TYPE_CHECKING

from .miscmodels import try_enum, Badge
from .iterators import PlayerIterator

if TYPE_CHECKING:
    from .players import Player


class BaseClan:
    """
    Abstract data class that represents base Clan objects

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
    __slots__ = ("tag", "name", "_client", "badge", "level", "_response_retry", "_raw_data")

    def __init__(self, *, data, client, **kwargs):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.badge = try_enum(Badge, data=data.get("badgeUrls"),
                              client=self._client)
        self.level = data.get("clanLevel")
        self._raw_data = data if client and client.raw_attribute else None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} tag={self.tag} name={self.name}>"

    def __eq__(self, other):
        return isinstance(other, BaseClan) and self.tag == other.tag

    @property
    def share_link(self) -> str:
        """str: A formatted link to open the clan in-game"""
        return f"https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{self.tag.strip('#')}"

    @property
    def members(self):
        # pylint: disable=missing-function-docstring
        return NotImplemented

    def get_detailed_members(self, cls: Type["Player"] = None,
                             load_game_data: bool = None) -> AsyncIterator["Player"]:
        """Get detailed player information for every player in the clan.

        This returns a :class:`PlayerIterator` which fetches all player
        tags in the clan in parallel.

        Example
        ---------

        .. code-block:: python3

            clan = await client.get_clan(clan_tag)

            async for player in clan.get_detailed_members():
                print(player.name)


        Yields
        ------
        :class:`Player`
            A full player object of a clan member.
        """
        if self.members is NotImplemented:
            return NotImplemented
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        return PlayerIterator(self._client,
                              (p.tag for p in self.members),
                              cls=cls,
                              load_game_data=load_game_data,
                              members=self.members_dict)


class BasePlayer:
    """An ABC that implements some common operations on players, regardless of type.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    """

    __slots__ = ("tag", "name", "_client", "_response_retry", "_raw_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} tag={self.tag} name={self.name}>"

    def __eq__(self, other):
        return isinstance(other, BasePlayer) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._raw_data = data if client and client.raw_attribute else None
        self.tag = data.get("tag")
        self.name = data.get("name")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the player in-game"""
        return f"https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{self.tag.strip('#')}"


class BaseDataClass:
    """Base class for simple data classes with standard repr.
    
    This class provides a default __repr__ implementation that displays
    the name and id attributes if they exist.
    """

    __slots__ = ()

    def __repr__(self):
        attrs = [
            ("name", getattr(self, "name", "Unknown")),
            ("id", getattr(self, "id", None)),
        ]
        # Filter out None values
        attrs = [(k, v) for k, v in attrs if v is not None]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs))


class LevelManager:
    """Handles level property and level data loading.
    
    This class manages the level state and triggers level-specific data loading
    when the level changes. Subclasses must implement _load_level_data().
    
    Attributes
    ----------
    level: :class:`int`
        The current level of the unit.
    max_level: :class:`int`
        The maximum level this unit can reach.
    is_max: :class:`bool`
        Whether the unit is at its maximum level.
    """

    __slots__ = (
        "_level",
        "_static_data",
        "max_level",
    )

    def __init__(self, initial_level: int, static_data: dict | None):

        #if the level is set to 0, initalize it as the lowest available level
        if initial_level == 0 and static_data:
            min_level = 1
            if static_data.get("levels"):
                min_level = static_data["levels"][0].get("level")
            initial_level = min_level

        self._level: int = initial_level
        self._static_data = static_data
        self.max_level: int = 0

    @property
    def level(self) -> int:
        """:class:`int`: The current level of the unit."""
        return self._level

    @level.setter
    def level(self, value: int):
        if not self._static_data:
            self._level = value
            return

        if value < 1:
            raise ValueError(f"Level must be greater than 1")

        self._level = value
        self._load_level_data()

    @property
    def is_max(self) -> bool:
        """:class:`bool`: Whether the unit is at its maximum level."""
        return self.max_level == self.level

    def _load_level_data(self):
        raise NotImplementedError("Subclasses must implement _load_level_data()")

    def __repr__(self):
        attrs = [
            ("name", getattr(self, "name", "Unknown")),
            ("level", self.level),
        ]
        if hasattr(self, "id"):
            attrs.insert(1, ("id", self.id))
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs))


class LeveledUnit(LevelManager):
    """Base class for units with level-dependent data and additional utilities.
    
    Extends LevelManager with townhall-specific level queries.
    """

    __slots__ = ()

    def get_max_level_for_townhall(self, townhall: int) -> int | None:
        """Get the maximum level for this unit at a given townhall level.

        Parameters
        ----------
        townhall: :class:`int`
            The townhall level to check.

        Returns
        -------
        Optional[:class:`int`]
            The maximum level this unit can reach at the given townhall level,
            or ``None`` if no static data is available.
        """
        if not self._static_data or not self._static_data["levels"]:
            return None

        max_level = None
        for level_data in self._static_data.get("levels", []):
            if level_data.get("required_townhall", 0) <= townhall:
                max_level = level_data.get("level")
            else:
                break

        return max_level
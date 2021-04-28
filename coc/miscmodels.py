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
from datetime import datetime
from typing import Any, Type, TypeVar, Optional

from .utils import from_timestamp

T = TypeVar("T")


def try_enum(_class: Type[T], data: Any, **kwargs) -> Optional[T]:
    """Helper function to create a class from the given data."""
    return data and _class(data=data, **kwargs)


class Achievement:
    """Represents a Clash of Clans Achievement.

    Attributes
    -----------
    name:
        :class:`str`: The name of the achievement.
    stars:
        :class:`int`: The current stars achieved for the achievement.
    value:
        :class:`int`: The number of X things attained for this achievement.
    target:
        :class:`int`: The number of X things required to complete this achievement.
    info:
        :class:`str`: Information regarding the achievement.
    completion_info:
        :class:`str`: Information regarding completion of the achievement.
    village:
        :class:`str`: Either ``home`` or ``builderBase``.
    """

    __slots__ = (
        "name",
        "stars",
        "value",
        "target",
        "info",
        "completion_info",
        "village",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("stars", self.stars),
            ("value", self.value),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.name: str = data["name"]
        self.stars: int = data["stars"]
        self.value: int = data["value"]
        self.target: int = data["target"]
        self.info: str = data["info"]
        self.completion_info: str = data["completionInfo"]
        self.village: str = data["village"]

    @property
    def is_builder_base(self) -> bool:
        """:class:`bool`: Returns a boolean which indicates if the achievement belongs to the builder base"""
        return self.village == "builderBase"

    @property
    def is_home_base(self) -> bool:
        """:class:`bool`: Returns a boolean which indicates if the achievement belongs to the home base"""
        return self.village == "home"

    @property
    def is_completed(self) -> bool:
        """:class:`bool`: Returns a boolean which indicates whether the achievement is completed (3 stars achieved)"""
        return self.stars == 3


class Troop:
    """Represents a Clash of Clans Troop.

    Attributes
    -----------
    name:
        :class:`str`: The name of the troop.
    level:
        :class:`int`: The level of the troop.
    max_level:
        :class:`int`: The overall max level of the troop; excluding townhall limitations.
    village:
        :class:`str`: Either ``home`` or ``builderBase``.
    is_active:
        :class:`bool`: Returns a boolean which indicates whether a super troop is active.
    """

    __slots__ = (
        "name",
        "level",
        "max_level",
        "village",
        "is_active",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("level", self.level),
            ("is_active", self.is_active),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data):
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]
        self.is_active: bool = data.get("superTroopIsActive")

    @property
    def is_max(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop is the max level"""
        return self.max_level == self.level

    @property
    def is_builder_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop belongs to the builder base."""
        return self.village == "builderBase"

    @property
    def is_home_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop belongs to the home base."""
        return self.village == "home"


class Hero:
    """Represents a Clash of Clans Hero.

    Attributes
    -----------
    name:
        :class:`str`: The name of the hero.
    level:
        :class:`int`: The level of the hero.
    max_level:
        :class:`int`: The overall max level of the hero, excluding townhall limitations.
    village:
        :class:`str`: Either ``home`` or ``builderBase``.
    """

    __slots__ = (
        "name",
        "level",
        "max_level",
        "village",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("level", self.level),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]

    @property
    def is_max(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the hero is the max level."""
        return self.level == self.max_level

    @property
    def is_builder_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the hero belongs to the builder base."""
        return self.village == "builderBase"

    @property
    def is_home_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the hero belongs to the home base."""
        return self.village == "home"


class Spell:
    """Represents a Clash of Clans Spell.

    Attributes
    -----------
    name:
        :class:`str`: The name of the spell.
    level:
        :class:`int`: The level of the spell.
    max_level:
        :class:`int`: The overall max level of the spell, excluding townhall limitations.
    village:
        :class:`str`: Either ``home`` or ``builderBase``.
    """

    __slots__ = ("name", "level", "max_level", "village")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("level", self.level),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]

    @property
    def is_max(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the spell is the max level."""
        return self.level == self.max_level

    @property
    def is_builder_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the spell belongs to the builder base."""
        return self.village == "builderBase"

    @property
    def is_home_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the spell belongs to the home base."""
        return self.village == "home"


class Location:
    """Represents a Clash of Clans Location

    Attributes
    -----------
    id:
        :class:`int` - The location ID
    name:
        :class:`str` - The location name
    is_country:
        :class:`bool` - Indicates whether the location is a country
    country_code:
        :class:`str` - The shorthand country code, if the location is a country
    localised_name:
        :class:`str` - A localised name of the location. The extent of the use of this is unknown at present.
    """

    __slots__ = ("id", "name", "is_country", "country_code", "localised_name")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("id", self.id),
            ("name", self.name),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __init__(self, *, data):
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        # pylint: disable=invalid-name
        data_get = data.get

        self.id: int = data_get("id")
        self.name: str = data_get("name")
        self.is_country: bool = data_get("isCountry")
        self.country_code: str = data_get("countryCode")
        self.localised_name: str = data_get("localizedName")


class League:
    """Represents a Clash of Clans League

    Attributes
    -----------
    id:
        :class:`int`: The league ID.
    name:
        :class:`str`: The league name.
    localised_name:
        :class:`str`: A localised name of the location. The extent of the use of this is unknown at present.
    localised_short_name:
        :class:`str`: A localised short name of the location. The extent of the use of this is unknown at present.
    icon:
        :class:`Icon`: The league's icon.
    """

    __slots__ = (
        "id",
        "name",
        "localised_short_name",
        "localised_name",
        "icon",
        "_client",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __init__(self, *, data, client):
        self._client = client
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        # pylint: disable=invalid-name
        data_get = data.get

        self.id: int = data_get("id")
        self.name: str = data_get("name")
        self.localised_name: str = data_get("localizedName")
        self.localised_short_name: str = data_get("localizedShortName")
        self.icon = try_enum(Icon, data=data_get("iconUrls"), client=self._client)


class Season:
    """Represents a Clash of Clans Player's Season."""

    # pylint: disable=invalid-name

    __slots__ = ("rank", "trophies", "id")

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.rank == other.rank
            and self.trophies == other.trophies
            and self.id == other.id
        )

    def __init__(self, *, data):
        self.rank: int = data.get("rank")
        self.trophies: int = data.get("trophies")
        self.id: int = data.get("id")


class LegendStatistics:
    """Represents the Legend Statistics for a player.

    Attributes
    -----------
    legend_trophies:
        :class:`int` - The player's legend trophies
    current_season:
        :class:`Season`: Legend statistics for this season.
    previous_season:
        :class:`Season`: Legend statistics for the previous season.
    best_season:
        :class:`Season`: Legend statistics for the player's best season.
    """

    __slots__ = ("legend_trophies", "current_season", "previous_season", "best_season")

    def __repr__(self):
        attrs = [
            ("legend_trophies", self.legend_trophies),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.best_season == other.best_season
            and self.current_season == other.current_season
        )

    def __init__(self, *, data):
        self.legend_trophies: int = data["legendTrophies"]
        self.current_season = try_enum(Season, data=data.get("currentSeason"))
        self.previous_season = try_enum(Season, data=data.get("previousSeason"))
        self.best_season = try_enum(Season, data=data.get("bestSeason"))


class Badge:
    """Represents a Clash Of Clans Badge.

    Attributes
    -----------
    small:
        :class:`str` - URL for a small sized badge (70x70).
    medium:
        :class:`str` - URL for a medium sized badge (200x200).
    large:
        :class:`str` - URL for a large sized badge (512x512).
    url:
        :class:`str` - Medium, the default URL badge size.
    """

    __slots__ = ("small", "medium", "large", "url", "_client")

    def __repr__(self):
        attrs = [
            ("url", self.url),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, client):
        self._client = client

        self.small: str = data.get("small")
        self.medium: str = data.get("medium")
        self.large: str = data.get("large")

        self.url: str = self.medium

    async def save(self, filepath, size=None) -> int:
        """
        |coro|

        Save this badge as a file-like object.

        Parameters
        -----------
        filepath: :class:`os.PathLike`
            The filename to save the badge to.
        size: Optional[:class:`str`]
            Either ``small``, ``medium`` or ``large``. The default is ``medium``.

        Returns
        --------
        The number of bytes written: :class:`int`

        Raises
        ------
        :exc:`HTTPException`:
            Saving the badge failed.
        :exc:`NotFound`:
            The URL was not found.
        """
        sizes = {"small": self.small, "medium": self.medium, "large": self.large}

        if size and size in sizes.keys():
            url = sizes[size]
        else:
            url = self.medium

        data = await self._client.http.get_data_from_url(url)

        with open(filepath, "wb") as file:
            return file.write(data)


class Icon:
    """Represents a Clash Of Clans Icon.

    Attributes
    -----------
    tiny:
        :class:`str`: URL for a tiny sized icon (32x32).
    small:
        :class:`str`: URL for a small sized icon (72x72).
    medium:
        :class:`str`: URL for a medium sized icon (288x288).
    url:
        :class:`str`: ``small``, the default URL icon size
    """

    __slots__ = ("small", "medium", "tiny", "url", "_client")

    def __repr__(self):
        attrs = [
            ("url", self.url),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, client):
        self._client = client

        self.tiny: str = data.get("tiny")
        self.small: str = data.get("small")
        self.medium: str = data.get("medium")

        self.url: str = self.medium

    async def save(self, filepath: str, size: Optional[str] = None) -> int:
        """
        |coro|

        Save this icon as a file-like object.

        Parameters
        -----------
        filepath: :class:`os.PathLike`
            The filename to save the badge to.
        size: Optional[:class:`str`]
            Either ``tiny``, ``small`` or ``medium``. The default is ``small``.

        Returns
        --------
        :class:`int`: The number of bytes written.

        Raises
        ------
        :exc:`HTTPException`:
            Saving the badge failed.
        :exc:`NotFound`:
            The URL was not found.
        """
        sizes = {"tiny": self.tiny, "small": self.small, "medium": self.medium}

        if size and size in sizes.keys():
            url = sizes[size]
        else:
            url = self.medium

        data = await self._client.http.get_data_from_url(url)

        with open(filepath, "wb") as file:
            return file.write(data)


class Timestamp:
    """Represents a Clash of Clans Timestamp

    Attributes
    -----------
    raw_time:
        :class:`str`: The raw timestamp string (ISO8601) as given by the API.
    """

    __slots__ = ("raw_time", "_data")

    def __repr__(self):
        attrs = [("time", self.time), ("seconds_until", self.seconds_until)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.raw_time == other.raw_time

    def __lt__(self, other):
        if not isinstance(other, Timestamp) or not isinstance(self, Timestamp):
            return NotImplemented

        return self.time < other.time

    def __le__(self, other):
        less_than = Timestamp.__lt__(other, self)
        if less_than is NotImplemented:
            return NotImplemented
        return not less_than

    def __init__(self, *, data):
        self.raw_time = data

    @property
    def time(self) -> datetime:
        """:class:`datetime`: Returns the timestamp as a UTC datetime object."""
        return from_timestamp(self.raw_time)

    @property
    def now(self) -> datetime:
        """:class:`datetime`: Returns the time in UTC now as a datetime object."""
        return datetime.utcnow()

    @property
    def seconds_until(self) -> int:
        """:class:`int`: Returns the number of seconds until the timestamp. This may be negative."""
        delta = self.time - self.now
        return int(delta.total_seconds())


class Label:
    """Represents a clan or player label.

    Attributes
    -----------
    id:
        :class:`int`: The label's unique ID as given by the API.
    name:
        :class:`str`: The label's name.
    badge:
        :class:`Badge`: The label's badge.
    """

    __slots__ = ("id", "name", "_client", "badge")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __init__(self, *, data, client):
        # pylint: disable=invalid-name
        self._client = client

        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.badge = try_enum(Icon, data=data.get("iconUrls"), client=self._client)


class WarLeague:
    """Represents a clan's CWL league.
    Attributes
    -----------
    id: :class:`int`: The league's unique ID
    name: :class:`str`: The league's name, as it appears in-game."""

    __slots__ = (
        "id",
        "name",
    )

    def __init__(self, *, data):
        # pylint: disable=invalid-name
        self.id: int = data["id"]
        self.name: str = data["name"]

    def __repr__(self):
        return "<%s id=%s name=%s>" % (self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(self, other.__class__) and other.id == self.id


class ChatLanguage:
    """Represents a clan's chat language.

    Attributes
    ----------
    id: :class:`int`: The language's unique ID
    name: :class:`str`: The language's full name, for example ``English``.
    language_code: :class:`str` The language's abbreviated code, for example ``EN``.
    """
    __slots__ = (
        "id",
        "name",
        "language_code"
    )

    def __init__(self, *, data):
        # pylint: disable=invalid-name
        self.id: int = data["id"]
        self.name: str = data["name"]
        self.language_code: str = data["languageCode"]

    def __repr__(self):
        return "<%s id=%s name=%s>" % (self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(self, other.__class__) and other.id == self.id


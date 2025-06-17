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

import coc
from .enums import ExtendedEnum, PlayerHouseElementType
from .utils import from_timestamp

T = TypeVar("T")


def try_enum(_class: Type[T], data: Any, **kwargs) -> Optional[T]:
    """Helper function to create a class from the given data."""
    if issubclass(_class, ExtendedEnum):
        return data and _class(data)
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


class LoadGameData:
    """Pass this into the ``load_game_data`` parameter of :class:`Client`.

    See :ref:`game_data` for more information.

    Parameters
    ----------
    always: bool
        Whether to always inject game metadata into objects.

    default: bool
        Always inject game metadata into objects, except when running events tasks.

    startup_only: bool
        Never automatically inject game metadata into objects, but load it up on startup regardless for use with
        the ``load_game_data`` parameter of :meth:`Client.get_player` or :meth:`Client.parse_army_link`.

    never: bool
        Never inject game metadata, and don't load it on startup.

    """
    always = False
    default = False
    startup_only = False
    never = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            try:
                getattr(self.__class__, key)
            except AttributeError:
                raise RuntimeError("%s was not a valid LoadGameData option.", key)
            else:
                setattr(self.__class__, key, value)


class TimeDelta:
    """Represents a Timedelta object corresponding to things that take time to do in the API.

    Some examples include:

    * Upgrade times
    * Training times
    * Cooldown times

    This object works in a very similar fashion to datetime's `timedelta <https://docs.python.org/3/library/datetime.html#timedelta-objects>`_
    object, but with a few more helpful attributes.

    .. note::

        You should not construct this yourself, instead use it from the attribute of an e.g. :class:`Troop` model.


    Attributes
    ----------
    days: int
        The number of days in the timedelta.
    hours: int
        The number of hours in the timedelta. This does not include days.
        For example, if an upgrade took 36 hours, the ``.days`` attribute would be 1, and ``.hours`` would be 12.
    minutes: int
        The number of minutes in the timedelta. The same logic applies as with hours.
    seconds: int
        The number of seconds in the timedelta. The same logic applies as with hours.

    """
    def __init__(self, days=0, hours=0, minutes=0, seconds=0):
        _days, _hours = divmod(hours, 24)
        _hours_left, _mins = divmod(minutes, 60)

        self.days = days + _days
        self.hours = hours + _hours + _hours_left
        self.minutes = minutes + _mins
        self.seconds = seconds

    def total_seconds(self):
        """Returns the total number of seconds in the time object.

        This is the addition of all days, hours, minutes, seconds.

        Returns
        -------
        int
            The number of seconds"""
        return self.days * 24 * 60 * 60 + \
               self.hours * 60 * 60 + \
               self.minutes * 60 + \
               self.seconds


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


class BaseLeague:
    """Represents a basic league.

    Attributes
    -----------
    id: :class:`int`: The league's unique ID
    name: :class:`str`: The league's name, as it appears in-game."""

    __slots__ = (
        "id",
        "name",
        "_client"
    )

    def __init__(self, *, data, client=None):
        # pylint: disable=invalid-name
        self.id: int = data["id"]
        self.name: str = data["name"]
        self._client = client

    def __repr__(self):
        return "<%s id=%s name=%s>" % (self.__class__.__name__, self.id, self.name)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(self, other.__class__) and other.id == self.id


class League(BaseLeague):
    """Represents a Clash of Clans League

    Attributes
    -----------
    id:
        :class:`int`: The league ID.
    name:
        :class:`str`: The league name.
    icon:
        :class:`Icon`: The league's icon.
    """

    __slots__ = (
        "icon",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __init__(self, *, data, client):
        super().__init__(data=data, client=client)
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        # pylint: disable=invalid-name
        data_get = data.get
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
    previous_builder_base_season:
        :class:`Season`: Legend statistics for the previous builder base season.
    best_builder_base_season:
        :class:`Season`: Legend statistics for the player's best builder base season.
    """

    __slots__ = ("legend_trophies", "current_season", "previous_season", "best_season", "previous_builder_base_season",
                 "best_builder_base_season")

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
            and self.best_builder_base_season == other.best_builder_base_season
            and self.previous_season == other.previous_season
            and self.previous_builder_base_season == self.previous_builder_base_season
        )

    def __init__(self, *, data):
        self.legend_trophies: int = data["legendTrophies"]
        self.current_season = try_enum(Season, data=data.get("currentSeason"))
        self.previous_season = try_enum(Season, data=data.get("previousSeason"))
        self.best_season = try_enum(Season, data=data.get("bestSeason"))
        self.previous_builder_base_season = try_enum(Season, data=data.get("previousBuilderBaseSeason"))
        self.best_builder_base_season = try_enum(Season, data=data.get("bestBuilderBaseSeason"))


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
    """

    __slots__ = ("small", "medium", "large", "_client")

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

    @property
    def url(self) -> str:
        """:class:`str`: the default icon URL. Returns the medium-sized icon URL if available.
        Falls back to small and large (in that order) if not"""
        return self.medium or self.small or self.large

    async def save(self, filepath, size=None) -> int:
        """
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
            url = self.url

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
    """

    __slots__ = ("small", "medium", "tiny", "_client")

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

    @property
    def url(self) -> str:
        """:class:`str`: the default icon URL. Returns the medium-sized icon URL if available.
        Falls back to small and tiny (in that order) if not"""
        return self.medium or self.small or self.tiny

    async def save(self, filepath: str, size: Optional[str] = None) -> int:
        """
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
            url = self.url

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
        """:class:`datetime`: Returns the time of the timestamp as a datetime object in UTC."""
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


class CapitalDistrict:
    """Represents a Clan Capital District.

    Attributes
    -----------
    id:
        :class:`int`: The district's unique ID as given by the API.
    name:
        :class:`str`: The district's name.
    hall_level:
        :class:`int`: The district's hall level
    """

    __slots__ = ("id", "name", "hall_level")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.id == other.id and \
               self.hall_level == other.hall_level

    def __init__(self, *, data, client):
        # pylint: disable=invalid-name
        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.hall_level: int = data.get("districtHallLevel")



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


class GoldPassSeason:
    """Represents a gold pass season.

    Attributes
    ----------
    start_time:
        :class:`Timestamp`: The gold pass season start time
    end_time:
        :class:`Timestamp`: The gold pass season end time
    duration:
        :class:`datetime.timedelta`: The duration of the gold pass season
    """
    __slots__ = ("start_time", "end_time", "duration")

    def __init__(self, *, data):
        self.start_time = try_enum(Timestamp, data.get("startTime"))
        self.end_time = try_enum(Timestamp, data.get("endTime"))
        self.duration = self.end_time.time - self.start_time.time

    def __eq__(self, other):
        return (isinstance(other, GoldPassSeason)
                and self.start_time == other.start_time
                and self.end_time == other.end_time)


class PlayerHouseElement:
    """Represents an element of a player house.

    Attributes
    ----------
    id:
        :class:`int`: The id of the house element
    type:
        :class:`PlayerHouseElementType`: The type of the house element
    """
    __slots__ = ("id", "type")

    def __init__(self, *, data):
        self.id = data.get("id")
        self.type = data.get("type") and PlayerHouseElementType(value=data["type"])

    def __eq__(self, other):
        return (isinstance(other, PlayerHouseElement)
                and self.id == other.id
                and self.type == other.type)
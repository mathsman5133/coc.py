# -*- coding: utf-8 -*-

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

from datetime import datetime

from .utils import from_timestamp


def try_enum(_class, data, default=None, **kwargs):
    """Helper function to create a class from the given data."""
    if data is None:
        return default
    return _class(data=data, **kwargs)


class EqualityComparable:
    """Allows comparison of 2 objects through identical data."""

    # pylint: disable=no-member, protected-access
    __slots__ = ()

    def __eq__(self, other):
        return isinstance(self, other.__class__) and self._data == other._data

    def __hash__(self):
        return hash(len(self._data))


class Achievement(EqualityComparable):
    """Represents a Clash of Clans Achievement.


    Attributes
    -----------
    player:
        :class:`SearchPlayer` - The player this achievement is assosiated with
    name:
        :class:`str` - The name of the achievement
    stars:
        :class:`int` - The current stars achieved for the achievement
    value:
        :class:`int` - The number of X things attained for this achievement
    target:
        :class:`int` - The number of X things required to complete this achievement
    info:
        :class:`str` - Information regarding the achievement
    completion_info:
        :class:`str` - Information regarding completion of the achievement
    village:
        :class:`str` - Either `home` or `builderBase`
    """

    __slots__ = (
        "player",
        "name",
        "stars",
        "value",
        "target",
        "info",
        "completion_info",
        "village",
        "_data",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("player", repr(self.player)),
            ("name", self.name),
            ("stars", self.stars),
            ("value", self.value),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data["name"]
        self.stars = data.get("stars")
        self.value = data["value"]
        self.target = data["target"]
        self.info = data["info"]
        self.completion_info = data.get("completionInfo")
        self.village = data["village"]

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the achievement belongs to the builder base
        """
        return self.village == "builderBase"

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the achievement belongs to the home base
        """
        return self.village == "home"

    @property
    def is_completed(self):
        """:class:`bool`: Indicates whether the achievement is completed (3 stars achieved)
        i"""
        return self.stars == 3


class Troop(EqualityComparable):
    """Represents a Clash of Clans Troop.

    Attributes
    -----------
    player:
        :class:`SearchPlayer` - player this troop is assosiated with
    name:
        :class:`str` - The name of the troop
    level:
        :class:`int` - The level of the troop
    max_level:
        :class:`int` - The overall max level of the troop, excluding townhall limitations
    village:
        :class:`str` - Either `home` or `builderBase`
    """

    __slots__ = ("player", "name", "level", "max_level", "village", "_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("player", repr(self.player)),
            ("name", self.name),
            ("level", self.level),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data["name"]
        self.level = data["level"]
        self.max_level = data["maxLevel"]
        self.village = data["village"]

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the troop is the max level
        """
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the troop belongs to the builder base
        """
        return self.village == "builderBase"

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the troop belongs to the home base
        """
        return self.village == "home"


class Hero(EqualityComparable):
    """Represents a Clash of Clans Hero.

    Attributes
    -----------
    player:
        :class:`SearchPlayer` - The player this hero is assosiated with
    name:
        :class:`str` - The name of the hero
    level:
        :class:`int` - The level of the hero
    max_level:
        :class:`int` - The overall max level of the hero, excluding townhall limitations
    village:
        :class:`str` - Either `home` or `builderBase`
    """

    __slots__ = ("player", "name", "level", "max_level", "village", "_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("player", repr(self.player)),
            ("name", self.name),
            ("level", self.level),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data["name"]
        self.level = data["level"]
        self.max_level = data["maxLevel"]
        self.village = data["village"]

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the hero is the max level
        """
        return self.level == self.max_level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the hero belongs to the builder base
        """
        return self.village == "builderBase"

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the hero belongs to the home base
        """
        return self.village == "home"


class Spell(EqualityComparable):
    """Represents a Clash of Clans Spell.

    Attributes
    -----------
    player:
        :class:`SearchPlayer` - The player this spell is assosiated with
    name:
        :class:`str` - The name of the spell
    level:
        :class:`int` - The level of the spell
    max_level:
        :class:`int` - The overall max level of the spell, excluding townhall limitations
    village:
        :class:`str` - Either `home` or `builderBase`
    """

    __slots__ = ("player", "name", "level", "max_level", "village", "_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("player", repr(self.player)),
            ("name", self.name),
            ("level", self.level),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data["name"]
        self.level = data["level"]
        self.max_level = data["maxLevel"]
        self.village = data["village"]

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the spell is the max level
        """
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the spell belongs to the builder base
        """
        return self.village == "builderBase"

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the spell belongs to the home base
        """
        return self.village == "home"


class Location(EqualityComparable):
    """Represents a Clash of Clans Location

    Attributes
    -----------
    id:
        :class:`str` - The location ID
    name:
        :class:`str` - The location name
    is_country:
        :class:`bool` - Indicates whether the location is a country
    country_code:
        :class:`str` - The shorthand country code, if the location is a country
    localised_name:
        :class:`str` - A localised name of the location. The extent of the use of this is unknown at present.
    """

    __slots__ = ("id", "name", "is_country", "country_code", "localised_name", "_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("id", self.id),
            ("name", self.name),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        # pylint: disable=invalid-name
        self._data = data

        self.id = data.get("id")
        self.name = data.get("name")
        self.is_country = data.get("isCountry")
        self.country_code = data.get("countryCode")
        self.localised_name = data.get("localizedName")


class League(EqualityComparable):
    """Represents a Clash of Clans League

    Attributes
    -----------
    id:
        :class:`str` - The league ID
    name:
        :class:`str` - The league name
    localised_name:
        :class:`str` - A localised name of the location. The extent of the use of this is unknown at present.
    localised_short_name:
        :class:`str` - A localised short name of the location. The extent of the use of this is unknown at present.
    """

    __slots__ = (
        "id",
        "name",
        "localised_short_name",
        "localised_name",
        "_data",
        "_http",
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, http):
        # pylint: disable=invalid-name
        self._data = data
        self._http = http

        self.id = data.get("id")
        self.name = data.get("name")
        self.localised_name = data.get("localizedName")
        self.localised_short_name = data.get("localizedShortName")

    @property
    def badge(self):
        """:class:`Badge`: The league's badge
        """
        return try_enum(Badge, data=self._data.get("iconUrls"), http=self._http)


class Season(EqualityComparable):
    """Represents a Clash of Clans Player's Season."""

    # pylint: disable=invalid-name

    __slots__ = ("rank", "trophies", "id")

    def __init__(self, *, data):
        self.rank = data.get("rank")
        self.trophies = data.get("trophies")
        self.id = data.get("id")


class LegendStatistics(EqualityComparable):
    """Represents the Legend Statistics for a player.

    Attributes
    -----------
    player:
        :class:`Player` - The player
    legend_trophies:
        :class:`int` - The player's legend trophies
    """

    __slots__ = ("player", "legend_trophies", "_data")

    def __repr__(self):
        attrs = [
            ("player", repr(self.player)),
            ("legend_trophies", self.legend_trophies),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.legend_trophies = data["legendTrophies"]

    @property
    def current_season(self):
        """:class:`int`: Legend trophies for this season.
        """
        return try_enum(Season, data=self._data.get("currentSeason"))

    @property
    def previous_season(self):
        """:class:`int`: Legend trophies for the previous season.
        """
        return try_enum(Season, data=self._data.get("previousSeason"))

    @property
    def best_season(self):
        """:class:`int`: Legend trophies for the player's best season.
        """
        return try_enum(Season, data=self._data.get("bestSeason"))


class Badge(EqualityComparable):
    """Represents a Clash Of Clans Badge.

    Attributes
    -----------
    small:
        :class:`str` - URL for a small sized badge
    medium:
        :class:`str` - URL for a medium sized badge
    large:
        :class:`str` - URL for a large sized badge
    url:
        :class:`str` - Medium, the default URL badge size
    """

    __slots__ = ("small", "medium", "large", "url", "_data", "_http")

    def __repr__(self):
        attrs = [
            ("url", self.url),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, http):
        self._http = http
        self._data = data

        self.small = data.get("small")
        self.medium = data.get("medium")
        self.large = data.get("large")

        self.url = self.medium

    async def save(self, filepath, size=None):
        """
        |coro|

        Save this badge as a file-like object.

        :param filepath: :class:`os.PathLike`
                    The filename to save the badge to
        :param size: Optional[:class:`str`] Either `small`, `medium` or `large`.
                                            The default is `medium`

        :raise HTTPException: Saving the badge failed

        :raise NotFound: The url was not found

        :return: :class:`int` The number of bytes written
        """
        sizes = {"small": self.small, "medium": self.medium, "large": self.large}

        if size and size in sizes.keys():
            url = sizes[size]
        else:
            url = self.medium

        data = self._http.get_data_from_url(url)

        with open(filepath, "wb") as file:
            return file.write(data)


class Timestamp(EqualityComparable):
    """Represents a Clash of Clans Timestamp

    Attributes
    -----------
    raw_time: :class:`str`: The raw timestamp string (ISO8601) as given by the API.
    """

    __slots__ = ("raw_time", "_data")

    def __repr__(self):
        attrs = [("time", self.raw_time), ("seconds_until", self.seconds_until)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._data = data
        self.raw_time = data

    @property
    def time(self):
        """:class:`datetime`: The timestamp as a UTC datetime object
        """
        return from_timestamp(self.raw_time)

    @property
    def now(self):
        """:class:`datetime`: The time in UTC now as a datetime object
        """
        return datetime.utcnow()

    @property
    def seconds_until(self):
        """:class:`int`: Number of seconds until the timestamp. This may be negative.
        """
        delta = self.time - self.now
        return delta.total_seconds()


class Label(EqualityComparable):
    """Represents a clan or player label.

    Attributes
    -----------
    id: :class:`int`: The label's unique ID as given by the API.
    name: :class:`str`: The label's name.
    """

    __slots__ = ("_data", "id", "name", "_http", "label_type")

    def __repr__(self):
        attrs = [("id", self.id), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, http):
        # pylint: disable=invalid-name
        self._http = http
        self._data = data

        self.id = data.get("id")
        self.name = data.get("name")

    @property
    def badge(self):
        """:class:`Badge` - The label's badge."""

        return try_enum(Badge, self._data.get("iconUrls"), http=self._http)


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
        self.id = data["id"]
        self.name = data["name"]

    def __repr__(self):
        return "<%s id=%s name=%s>" % self.__class__.__name__, self.id, self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, WarLeague) and other.id == self.id

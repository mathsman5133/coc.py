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

from itertools import chain

from .iterators import LeagueWarIterator
from .miscmodels import EqualityComparable, try_enum, Timestamp
from .utils import get, maybe_sort


class BaseWar(EqualityComparable):
    """Represents the most basic Clash of Clans War

    Attributes
    -----------
    team_size:
        :class:`int` - The number of players per clan in war
    clan_tag:
        :class:`str` - The clan tag passed for the request.
        This attribute is always present regardless of the war state.
    """

    __slots__ = ("team_size", "_data", "clan_tag", "_http")

    def __repr__(self):
        attrs = [
            ("clan_tag", self.clan_tag),
            ("clan", self.clan),
            ("opponent", self.opponent),
            ("size", self.team_size),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, clan_tag, http):
        self._http = http
        self._data = data
        self.team_size = data.get("teamSize")
        self.clan_tag = clan_tag

    @property
    def clan(self):
        """:class:`WarClan`: The offensive clan"""
        # pylint: disable=import-outside-toplevel
        clan = self._data.get("clan", {})
        if "tag" in clan:
            # at the moment, if the clan is in notInWar, the API returns
            # 'clan' and 'opponent' as dicts containing only badge urls of
            # no specific clan. very strange
            from .clans import WarClan  # hack because circular imports

            return WarClan(data=clan, war=self, http=self._http)
        return None

    @property
    def opponent(self):
        """:class:`WarClan`: The opposition clan"""
        # pylint: disable=import-outside-toplevel
        opponent = self._data.get("opponent", {})
        if "tag" in opponent:
            # same issue as clan
            from .clans import WarClan  # hack because circular imports

            return WarClan(data=opponent, war=self, http=self._http)
        return None


class WarLog(BaseWar):
    """Represents a Clash of Clans War Log Entry

    This class inherits :class:`BaseWar`, and thus all attributes
    of :class:`BaseWar` can be expected to be present.

    Attributes
    -----------
    result:
        :class:`str` - The result of the war - `win` or `loss`
    end_time:
        :class:`Timestamp` - The end time of the war as a Timestamp object
    """

    __slots__ = ("result", "end_time")

    def __init__(self, *, data, clan_tag, http):
        self.result = data.get("result")
        self.end_time = try_enum(Timestamp, data.get("endTime"))
        super(WarLog, self).__init__(data=data, clan_tag=clan_tag, http=http)


class ClanWar(BaseWar):
    """Represents a Current Clash of Clans War

    This class inherits :class:`BaseWar`, and thus all attributes
    of :class:`BaseWar` can be expected to be present.

    Attributes
    -----------
    state:
        :class:`str` - The clan's current war state
    preparation_start_time:
        :class:`Timestamp` - The start time of preparation day as a Timestamp object
    start_time:
        :class:`Timestamp` - The start time of battle day as a Timestamp object
    end_time:
        :class:`Timestamp` - The end time of battle day as a Timestamp object
    """

    __slots__ = ("state", "preparation_start_time", "start_time", "end_time")

    def __init__(self, *, data, clan_tag, http):
        self.state = data.get("state")
        self.preparation_start_time = try_enum(Timestamp, data.get("preparationStartTime"))
        self.start_time = try_enum(Timestamp, data.get("startTime"))
        self.end_time = try_enum(Timestamp, data.get("endTime"))

        super(ClanWar, self).__init__(data=data, clan_tag=clan_tag, http=http)

    def _get_attacks(self):
        return chain(self.clan.iterattacks, self.opponent.iterattacks)

    @property
    def iterattacks(self, sort=True):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all attacks this war
        """
        return maybe_sort(self._get_attacks(), sort, itr=True)

    @property
    def attacks(self, sort=True):
        """List[:class:`WarAttack`]: A list of all attacks this war
        """
        return maybe_sort(self._get_attacks(), sort)

    @property
    def itermembers(self):
        """|iter|

        Returns an iterable of :class:`WarMember`: all members this war
        """
        return chain(self.clan.itermembers, self.opponent.itermembers)

    @property
    def members(self):
        """List[:class:`WarMember`]: A list of all members this war"""
        return list(self.itermembers)

    @property
    def type(self):
        """:class:`str`: Either ``friendly`` or ``random`` - the war type.
        Returns ``None`` if the clan is not in war.

        Possibilities for the length of preparation time for a friendly war include:
        15 minutes, 30 minutes, 1 hour, 2 hours, 4 hours, 6 hours, 8 hours, 12 hours,
        16 hours, 20 hours or 24 hours.
        """
        if not self.start_time:
            return None

        prep_list = [
            15 * 60,
            30 * 60,
            60 * 60,
            2 * 60 * 60,
            4 * 60 * 60,
            6 * 60 * 60,
            8 * 60 * 60,
            12 * 60 * 60,
            16 * 60 * 60,
            20 * 60 * 60,
            24 * 60 * 60,
        ]
        if (self.start_time.time - self.preparation_start_time.time).seconds in prep_list:
            return "friendly"
        return "random"

    @property
    def status(self):
        """:class:`str`: The war status, based off the home clan.

        Strings returned are determined by result and state and are below:

        +------------+-------------+
        | ``inWar``  | ``warEnded``|
        +------------+-------------+
        | ``winning``| ``won``     |
        +------------+-------------+
        | ``tied``   | ``tie``     |
        +------------+-------------+
        | ``losing`` | ``lost``    |
        +------------+-------------+
        """
        # pylint: disable=too-many-return-statements
        if self.state == "inWar":
            if self.clan.stars > self.opponent.stars:
                return "winning"
            if self.clan.stars == self.opponent.stars:
                if self.clan.destruction > self.opponent.destruction:
                    return "winning"
                if self.clan.destruction == self.opponent.destruction:
                    return "tied"

            return "losing"

        if self.state == "warEnded":
            if self.clan.stars > self.opponent.stars:
                return "won"
            if self.clan.stars == self.opponent.stars:
                if self.clan.destruction > self.opponent.destruction:
                    return "won"
                if self.clan.destruction == self.opponent.destruction:
                    return "tie"
                return "lost"

            return "lost"

        return ""

    def get_member(self, **attrs):
        """Returns the first :class:`WarMember` that meets the attributes passed

        This will return the first member matching the attributes passed.

        An example of this looks like:

        .. code-block:: python3

            member = ClanWar.get_member(tag='tag')

        This search implements the :func:`coc.utils.get` function
        """
        return get(self.itermembers, **attrs)


class WarAttack(EqualityComparable):
    """
    Represents a Clash of Clans War Attack

    Attributes
    -----------
    war:
        :class:`ClanWar` - The war this attack belongs to
    stars:
        :class:`int` - The stars achieved
    destruction:
        :class:`float` - The destruction achieved as a percentage (of 100)
    order:
        :class:`int` - The attack order in this war
    attacker_tag:
        :class:`str` - The attacker tag
    defender_tag:
        :class:`str` - The defender tag
    """

    __slots__ = (
        "war",
        "member",
        "stars",
        "destruction",
        "order",
        "attacker_tag",
        "defender_tag",
        "_data",
    )

    def __repr__(self):
        attrs = [
            ("war", repr(self.war)),
            ("member", repr(self.member)),
            ("stars", self.stars),
            ("destruction", self.destruction),
            ("order", self.order),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, war, member):
        self._data = data

        self.war = war
        self.member = member
        self.stars = data["stars"]
        self.destruction = data["destructionPercentage"]
        self.order = data["order"]
        self.attacker_tag = data["attackerTag"]
        self.defender_tag = data["defenderTag"]

    @property
    def attacker(self):
        """:class:`WarMember`: The attacker."""
        return self.war.get_member(tag=self.attacker_tag)

    @property
    def defender(self):
        """:class:`WarMember`: The defender."""
        return self.war.get_member(tag=self.defender_tag)


class LeagueGroup(EqualityComparable):
    """Represents a Clash of Clans League Group

    Attributes
    -----------
    state:
        :class:`str` - The current state of the league group (`inWar`, `preparation` etc.)
    season:
        :class:`str` - The current season of the league group
    """

    __slots__ = ("state", "season", "_rounds", "_data", "_http")

    def __repr__(self):
        attrs = [
            ("state", self.state),
            ("season", self.season),
            ("clans", ", ".join(repr(n) for n in self.iterclans)),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, http):
        self._data = data
        self._http = http

        self._rounds = []
        self.state = data.get("state")
        self.season = data.get("season")

    @property
    def iterclans(self):
        """|iter|

        Returns an iterable of class:`LeagueClan`: all participating clans
        """
        # pylint: disable=import-outside-toplevel
        from .clans import LeagueClan  # hack because circular imports

        return iter(LeagueClan(data=cdata, http=self._http) for cdata in self._data.get("clans", []))

    @property
    def clans(self):
        """List[class:`LeagueClan`]: A list of participating clans.
        """
        return list(self.iterclans)

    @property
    def number_of_rounds(self):
        """:class:`int` The number of rounds this league group contains."""
        return len(self._data["rounds"])

    @property
    def rounds(self):
        """List[List[]]: A list of lists containing all war tags for each round.

        .. note:

            This only returns the current or past rounds. Any future rounds filled with #0 war tags will not appear.

            To find the number of rounds in this season, use :attr:`LeagueGroup.number_of_rounds`.

        """
        # the API returns a list and the rounds that haven't started contain war tags of #0 (not sure why)...
        # we want to get only the valid rounds
        return [n["warTags"] for n in self._data["rounds"] if n["warTags"][0] != "#0"]

    def get_wars(self, round_index: int = -1, cache: bool = True, fetch: bool = True, update_cache: bool = True):
        """Get war information for every war in a league round.
        This will return an AsyncIterator of :class:`LeagueWar`.

        Example
        --------

        .. code-block:: python3

            group = await client.get_league_group('clan_tag')

            async for war in group.get_wars():
                print(war.clan_tag)

        Parameters
        ------------
        round_index: Optional[:class:`int`] - Indicates the round number to get wars from.
                     These rounds can be found with :attr:`LeagueGroup.rounds` and defaults
                     to the most recent round (index of -1).
        cache: Optional[:class:`bool`] Indicates whether to search
               the cache before making an HTTP request
        fetch: Optional[:class:`bool`] Indicates whether an HTTP call
               should be made if cache is empty.
               Defaults to ``True``. If this is ``False`` and item in cache was not found,
               ``None`` will be returned
        update_cache: Optional[:class:`bool`] Indicates whether the client should update
                      the cache when requesting members. Defaults to ``True``.
                      This should only be set to ``False``
                      if you do not require the cache at all.

        Returns
        ---------
        AsyncIterator of :class:`LeagueWar`
        """
        tags = iter(n for n in self.rounds[round_index])
        return LeagueWarIterator(
            client=self._http.client, tags=tags, cache=cache, fetch=fetch, update_cache=update_cache
        )


class LeagueWar(ClanWar):
    """Represents a Clash of Clans LeagueWar

    This class inherits both :class:`BaseWar` and :class:`ClanWar`,
    and thus all attributes of these classes can be expected to be present.

    Attributes
    -----------
    tag:
        :class:`str` - The war tag
    """

    __slots__ = ("tag",)

    def __init__(self, *, data, http):
        self.tag = data.get("tag")
        clan_tag = ""
        super(LeagueWar, self).__init__(data=data, clan_tag=clan_tag, http=http)
        self.clan_tag = getattr(self.clan, "tag", clan_tag)

    @property
    def type(self):
        """:class:`str`: The war type. For league wars, this is ``cwl``.
        """
        return "cwl"


class LeagueWarLogEntry(EqualityComparable):
    """Represents a Clash of Clans War Log entry for a League Season

    Attributes
    -----------
    end_time:
        :class:`Timestamp` - The end time of the war as a Timestamp object
    team_size:
        :class:`int` - The number of players per clan in war
    clan:
        :class:`Clan` - The offensive clan. Note this is only a :class:`Clan`,
        unlike that of a :class:`WarLog`
    enemy_stars:
        :class:`int` - Total enemy stars for all wars
    attack_count:
        :class:`int` - The total attacks completed by your clan over all wars
    stars:
        :class:`int` The total stars by your clan over all wars
    destruction:
        :class:`float` - The total destruction by your clan over all wars
    clan_level:
        :class:`int` - Your clan level.
    clan_tag:
        :class:`str` - The clan tag searched for.
        This attribute is always present regardless of the state of war.
    """

    __slots__ = (
        "end_time",
        "team_size",
        "clan",
        "enemy_stars",
        "attack_count",
        "stars",
        "destruction",
        "clan_level",
        "clan_tag",
    )

    def __repr__(self):
        attrs = [
            ("clan_tag", self.clan_tag),
            ("clan", repr(self.clan)),
            ("size", self.team_size),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, clan_tag, http):
        # pylint: disable=protected-access, import-outside-toplevel
        self.end_time = try_enum(Timestamp, data.get("endTime"))
        self.team_size = data.get("teamSize")

        from .clans import Clan  # hack because circular imports

        self.clan = try_enum(Clan, data.get("clan"), http=http)
        self.clan_tag = clan_tag

        try:
            self.enemy_stars = data["opponent"]["stars"]
        except KeyError:
            self.enemy_stars = None

        if self.clan:
            self.attack_count = self.clan._data.get("attacks")
            self.stars = self.clan._data.get("stars")
            self.destruction = self.clan._data.get("destructionPercentage")
            self.clan_level = self.clan._data.get("clanLevel")

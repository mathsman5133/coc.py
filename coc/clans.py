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

from .iterators import PlayerIterator
from .miscmodels import EqualityComparable, try_enum, Location, Badge, Label, WarLeague
from .utils import get, maybe_sort


class Clan(EqualityComparable):
    """Represents the most stripped down version of clan info.
    All other clan classes inherit this.

    Attributes
    -----------
    tag : str
        The clan tag.
    name : str
        The clan name.
    level:
        :class:`int` - The clan level.
    """

    __slots__ = ("tag", "name", "level", "_data", "_http")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ("tag", self.tag),
            ("name", self.name),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, http):
        self._http = http
        self._data = data
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.level = data.get("clanLevel")

    @property
    def badge(self):
        """:class:`Badge` - The clan badges
        """
        return try_enum(Badge, self._data.get("badgeUrls"), http=self._http)

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the clan in-game
        """
        return "https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{}".format(self.tag.strip("#"))


class BasicClan(Clan):
    """Represents a Basic Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Clan`, and thus all attributes
    of :class:`Clan` can be expected to be present.

    Attributes
    -----------
    points:
        :class:`int` - The clan trophy points.
    versus_points:
        :class:`int` - The clan versus trophy points.
    member_count:
        :class:`int` - The member count of the clan
    rank:
        :class:`int` - The clan rank for it's location this season
    previous_rank:
        :class:`int` - The clan rank for it's location in the previous season
    """

    __slots__ = (
        "points",
        "versus_points",
        "member_count",
        "rank",
        "previous_rank",
    )

    def __init__(self, *, data, http):
        super().__init__(data=data, http=http)

        self.points = data.get("clanPoints")
        self.versus_points = data.get("clanVersusPoints")
        self.member_count = data.get("members")
        self.rank = data.get("rank")
        self.previous_rank = data.get("previous_rank")

    @property
    def location(self):
        """:class:`Location` - The clan's location
        """
        return try_enum(Location, self._data.get("location"))


class SearchClan(BasicClan):
    """Represents a Searched Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits both :class:`Clan` and :class:`BasicClan`,
    and thus all attributes of these classes can be expected to be present.

    Attributes
    -----------
    type:
        :class:`str` - The clan type: open, closed, invite-only etc.
    required_trophies:
        :class:`int` - The required trophies to join
    war_frequency:
        :class:`str` - The war frequency of the clan
    war_win_streak:
        :class:`int` - The current war win streak of the clan
    war_wins:
        :class:`int` - The total war wins of the clan
    war_ties:
        :class:`int` - The total war ties of the clan
    war_losses:
        :class:`int` - The total war losses of the clan
    public_war_log:
        :class:`bool` - Indicates whether the war log is public
    description:
        :class:`str` - The clan description
    war_league:
        :class:`WarLeague` - the clan's CWL league name and ID.
    """

    __slots__ = (
        "type",
        "required_trophies",
        "war_frequency",
        "war_win_streak",
        "war_wins",
        "war_ties",
        "war_losses",
        "public_war_log",
        "description",
        "war_league",
    )

    def __init__(self, *, data, http):
        super().__init__(data=data, http=http)

        self.type = data.get("type")
        self.required_trophies = data.get("requiredTrophies")
        self.war_frequency = data.get("warFrequency")
        self.war_win_streak = data.get("warWinStreak")
        self.war_wins = data.get("warWins")
        self.war_ties = data.get("warTies")
        self.war_losses = data.get("warLosses")
        self.public_war_log = data.get("isWarLogPublic")
        self.description = data.get("description", "")
        self.war_league = try_enum(WarLeague, data.get("warLeague"))

    @property
    def iterlabels(self):
        """|iter|

        Returns an iterable of :class:`Label`: the player's labels.
        """
        return iter(Label(data=ldata, http=self._http) for ldata in self._data.get("labels", []))

    @property
    def labels(self):
        """List[:class:`Label`]: List of the player's labels."""
        return list(self.iterlabels)

    @property
    def itermembers(self):
        """|iter|

        Returns an iterable of :class:`BasicPlayer`: A list of clan members.
        """
        # pylint: disable=import-outside-toplevel
        from .players import BasicPlayer  # hack because circular imports

        return iter(BasicPlayer(mdata, self._http, self) for mdata in self._data.get("memberList", []))

    @property
    def members(self):
        """List[:class:`BasicPlayer`]: A list of clan members
        """
        return list(self.itermembers)

    @property
    def members_dict(self, attr="tag"):
        r"""A dict of clan members by tag.

        For Example:

        .. code-block:: python3

            members_dict = {attr_value: member for member in clan_members}

            # calling SearchClan.members_dict would give:
            members_dict = {member.tag: member for member in clan.members}

            # calling SearchClan.members_dict(attr="name") would give:
            members_dict = {member.name: member for member in clan.members}

        Pass in an attribute of :class:`BasicPlayer` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.itermembers}

    def get_member(self, **attrs):
        """Returns the first :class:`BasicPlayer` that meets the attributes passed

        This will return the first member matching the attributes passed.

        An example of this looks like:

        .. code-block:: python3

            member = SearchClan.get_member(tag='tag')

        This search implements the :func:`coc.utils.get` function
        """
        return get(self.itermembers, **attrs)

    def get_detailed_members(self, cache: bool = False, fetch: bool = True, update_cache: bool = True):
        """Get detailed player information for every player in the clan.
        This will return an AsyncIterator of :class:`SearchPlayer`.

        Example
        --------

        .. code-block:: python3

            clan = await client.get_clan('tag')

            async for player in clan.get_detailed_members(cache=True):
                print(player.name)

        :param cache: Optional[:class:`bool`] Indicates whether to search
                        the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call
                        should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param update_cache: Optional[:class:`bool`] Indicates whether the client should update
                                the cache when requesting members. Defaults to ``True``.
                                This should only be set to ``False``
                                if you do not require the cache at all.
        :return: AsyncIterator of :class:`SearchPlayer`
        """
        tags = iter(n.tag for n in self.itermembers)
        return PlayerIterator(self._http.client, tags, cache, fetch, update_cache)


class WarClan(Clan):
    """Represents a War Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Clan`, and thus all attributes
    of :class:`Clan` can be expected to be present.

    Attributes
    -----------
    stars:
        :class:`int` - Number of stars by clan this war
    destruction:
        :class:`float` - Destruction as a percentage
    exp_earned:
        :class:`int` - Total XP earned by clan this war
    attacks_used:
        :class:`int` - Total attacks used by clan this war
    max_stars:
        :class:`int` - Total possible stars achievable
    """

    __slots__ = (
        "_war",
        "level",
        "attack_count",
        "stars",
        "destruction",
        "exp_earned",
        "attacks_used",
        "total_attacks",
        "max_stars",
    )

    def __init__(self, *, data, war, http):
        super(WarClan, self).__init__(data=data, http=http)

        self._war = war
        self.level = data.get("clanLevel")
        self.destruction = data.get("destructionPercentage")
        self.exp_earned = data.get("expEarned")

        self.attacks_used = data.get("attacks")
        self.total_attacks = self._war.team_size * 2
        self.stars = data.get("stars")
        self.max_stars = self._war.team_size * 3

    @property
    def itermembers(self):
        """|iter|

        Returns an iterable of :class:`WarMember`: all clan members in war.
        """
        # pylint: disable=import-outside-toplevel
        from .players import WarMember  # hack because circular imports

        return iter(WarMember(data=mdata, war=self._war, clan=self) for mdata in self._data.get("members", []))

    @property
    def members(self):
        """List[:class:`WarMember`]: List of all clan members in war"""
        return list(self.itermembers)

    @property
    def members_dict(self, attr="tag"):
        """A dict of clan members in war by tag.

        See :attr:`SearchClan.member_dict` for more info on what this returns.

        Pass in an attribute of :class:`WarMember` to get that attribute as the key.
        """
        return {getattr(m, attr): m for m in self.itermembers}

    def _get_attacks(self):
        return chain.from_iterable(m.iterattacks for m in self.itermembers)

    @property
    def iterattacks(self, sort=True):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all attacks used by the clan this war.
        """
        return maybe_sort(self._get_attacks(), sort, itr=True)

    @property
    def attacks(self, sort=True):
        """List[:class:`WarAttack`]: List of all attacks used this war.
        """
        return maybe_sort(self._get_attacks(), sort)

    def _get_defenses(self):
        return chain.from_iterable(iter(n.iterdefenses for n in self.itermembers))

    @property
    def iterdefenses(self, sort=True):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all defenses by clan members this war.
        """
        return maybe_sort(self._get_defenses(), sort, itr=True)

    @property
    def defenses(self, sort=True):
        """List[:class:`WarAttack`]: List of all defenses by clan members this war.
        """
        return maybe_sort(self._get_defenses(), sort)


class LeagueClan(BasicClan):
    """Represents a Clash of Clans League Clan

    This class inherits both :class:`Clan` and :class:`BasicClan`,
    and thus all attributes of these classes can be expected to be present.

    """

    @property
    def itermembers(self):
        """|iter|

        Returns an iterable of :class:`LeaguePlayer`:
        all players participating in this league season
        """
        # pylint: disable=cyclic-import, import-outside-toplevel
        from .players import LeaguePlayer  # hack because circular imports

        return iter(LeaguePlayer(data=mdata) for mdata in self._data.get("members", []))

    @property
    def members(self):
        """List[:class:`LeaguePlayer`} A list of players participating in this league season
        """
        return list(self.itermembers)

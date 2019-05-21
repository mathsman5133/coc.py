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
from operator import attrgetter

from .miscmodels import EqualityComparable, try_enum, Timestamp
from .utils import get


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
    __slots__ = ('team_size', '_data', 'clan_tag')

    def __init__(self, *, data, clan_tag):
        self._data = data
        self.team_size = data.get('teamSize')
        self.clan_tag = clan_tag

    @property
    def clan(self):
        """:class:`WarClan`: The offensive clan"""
        clan = self._data.get('clan', {})
        if 'tag' in clan:
            # at the moment, if the clan is in notInWar, the API returns
            # 'clan' and 'opponent' as dicts containing only badge urls of
            # no specific clan. very strange
            from .clans import WarClan  # hack because circular imports
            return WarClan(data=clan, war=self)

    @property
    def opponent(self):
        """:class:`WarClan`: The opposition clan"""
        opponent = self._data.get('opponent', {})
        if 'tag' in opponent:
            # same issue as clan
            from .clans import WarClan  # hack because circular imports
            return WarClan(data=opponent, war=self)


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
    __slots__ = ('result', 'end_time')

    def __init__(self, *, data, clan_tag):
        self.result = data.get('result')
        self.end_time = try_enum(Timestamp, data.get('endTime'))
        super(WarLog, self).__init__(data=data, clan_tag=clan_tag)


class CurrentWar(BaseWar):
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
    __slots__ = ('state', 'preparation_start_time',
                 'start_time', 'end_time')

    def __init__(self, *, data, clan_tag):
        self.state = data.get('state')
        self.preparation_start_time = try_enum(Timestamp, data.get('preparationStartTime'))
        self.start_time = try_enum(Timestamp, data.get('startTime'))
        self.end_time = try_enum(Timestamp, data.get('endTime'))

        super(CurrentWar, self).__init__(data=data, clan_tag=clan_tag)

    @property
    def _attacks(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all attacks this war"""
        return chain(self.clan._attacks, self.opponent._attacks)

    @property
    def attacks(self):
        """List[:class:`WarAttack`]: A list of all attacks this war"""
        a = list(self._attacks)
        a.sort(key=attrgetter('order'))
        return a

    @property
    def _members(self):
        """|iter|

        Returns an iterable of :class:`WarMember`: all members this war"""
        return chain(self.clan._members, self.opponent._members)

    @property
    def members(self):
        """List[:class:`WarMember`]: A list of all members this war"""
        return list(self._members)

    def get_member(self, **attrs):
        """Returns the first :class:`WarMember` that meets the attributes passed

        This will return the first member matching the attributes passed.

        An example of this looks like:

        .. code-block:: python3

            member = CurrentWar.get_member(tag='tag')

        This search implements the :func:`coc.utils.get` function
        """
        return get(self._members, **attrs)


class WarAttack(EqualityComparable):
    """
    Represents a Clash of Clans War Attack

    Attributes
    -----------
    war:
        :class:`War` - The war this attack belongs to
    stars:
        :class:`int` - The stars achieved
    destruction:
        :class:`float` - The destruction achieved as a percentage (of 100)
    order:
        :class:`int` - The attack order in this war
    attacker_tag:
        :class:`int` - The attacker tag
    defender_tag:
        :class:`int` - The defender tag
    """
    __slots__ = ('war', 'member', 'stars',
                 'destruction', 'order',
                 'attacker_tag', 'defender_tag', '_data')

    def __init__(self, *, data, war, member):
        self._data = data

        self.war = war
        self.member = member
        self.stars = data['stars']
        self.destruction = data['destructionPercentage']
        self.order = data['order']
        self.attacker_tag = data['attackerTag']
        self.defender_tag = data['defenderTag']

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
    __slots__ = ('state', 'season', '_rounds', '_data')

    def __init__(self, *, data):
        self._data = data

        self._rounds = []
        self.state = data.get('state')
        self.season = data.get('season')

    @property
    def _clans(self):
        """|iter|

        Returns an iterable of class:`LeagueClan`: all participating clans"""
        from .clans import LeagueClan  # hack because circular imports
        return iter(LeagueClan(data=cdata) for cdata in self._data.get('clans', []))

    @property
    def clans(self):
        """List[class:`LeagueClan`]: A list of participating clans."""
        return list(self._clans)

    @property
    def rounds(self):
        """List[List[]]: A list of lists containing all war tags for each round"""
        # TODO: Find a better method of doing this
        rounds = []
        for rdata in self._data.get('rounds', []):
            rounds.append(rdata['warTags'])

        return rounds


class LeagueWar(CurrentWar):
    """Represents a Clash of Clans LeagueWar

    This class inherits both :class:`BaseWar` and :class:`CurrentWar`,
    and thus all attributes of these classes can be expected to be present.

    Attributes
    -----------
    tag:
        :class:`str` - The war tag
    """
    def __init__(self, *, data):
        self.tag = data.get('tag')
        clan_tag = ''
        super(LeagueWar, self).__init__(data=data, clan_tag=clan_tag)
        self.clan_tag = getattr(self.clan, 'tag')


class LeagueWarLogEntry(EqualityComparable):
    """Represents a Clash of Clans War Log entry for a League Season

    Attributes
    -----------
    end_time:
        :class:`Timestamp` - The end time of the war as a Timestamp object
    team_size:
        :class:`int` - The number of players per clan in war
    clan:
        :class:`Clan` - The offensive clan. Note this is only a :class:`Clan`, unlike that of a :class:`WarLog`
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

    __slots__ = ('end_time', 'team_size', 'clan', 'enemy_stars',
                 'attack_count', 'stars', 'destruction', 'clan_level',
                 'clan_tag')

    def __init__(self, *, data, clan_tag):
        self.end_time = try_enum(Timestamp, data.get('endTime'))
        self.team_size = data.get('teamSize')
        from .clans import Clan  # hack because circular imports
        self.clan = try_enum(Clan, data.get('clan'))
        self.clan_tag = clan_tag
        try:
            self.enemy_stars = data['opponent']['stars']
        except KeyError:
            self.enemy_stars = None

        if self.clan:
            self.attack_count = self.clan._data.get('attacks')
            self.stars = self.clan._data.get('stars')
            self.destruction = self.clan._data.get('destructionPercentage')
            self.clan_level = self.clan._data.get('clanLevel')

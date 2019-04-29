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
from operator import attrgetter
from itertools import chain

from .utils import get, from_timestamp


def try_enum(_class, data):
    if data is None:
        return None
    return _class(data=data)


class Clan:
    """Represents the most stripped down version of clan info.
    All other clan classes inherit this.

    Attributes
    ------------
    tag:
        :class:`str` - The clan tag
    name:
        :class:`str` - The clan name
    """
    __slots__ = ('tag', 'name', '_data')

    def __init__(self, *, data):
        self._data = data
        self.tag = data.get('tag')
        self.name = data.get('name')

    @property
    def badge(self):
        """:class:`Badge` - The clan badges"""
        return try_enum(Badge, self._data.get('badgeUrls'))

    def __str__(self):
        return self.name


class BasicClan(Clan):
    """Represents a Basic Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Clan`, and thus all attributes
    of :class:`Clan` can be expected to be present.

    Attributes
    -----------
    level:
        :class:`int` - The clan level.
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
    __slots__ = ('level', 'points', 'versus_points',
                 'member_count', 'rank', 'previous_rank')

    def __init__(self, *, data):
        super().__init__(data=data)

        self.level = data.get('clanLevel')
        self.points = data.get('clanPoints')
        self.versus_points = data.get('clanVersusPoints')
        self.member_count = data.get('members')
        self.rank = data.get('rank')
        self.previous_rank = data.get('previous_rank')

    @property
    def location(self):
        """:class:`Location` - The clan's location"""
        return try_enum(Location, self._data.get('location'))


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
    """
    __slots__ = ('type', 'required_trophies', 'war_frequency', 'war_win_streak',
                 'war_wins', 'war_ties', 'war_losses', 'public_war_log',
                 'description', '_http')

    def __init__(self, *, data, http):
        super().__init__(data=data)

        self._http = http
        self.type = data.get('type')
        self.required_trophies = data.get('requiredTrophies')
        self.war_frequency = data.get('warFrequency')
        self.war_win_streak = data.get('warWinStreak')
        self.war_wins = data.get('warWins')
        self.war_ties = data.get('warTies')
        self.war_losses = data.get('warLosses')
        self.public_war_log = data.get('isWarLogPublic')
        self.description = data.get('description', '')

    @property
    def _members(self):
        """|iter|

        Returns an iterable of :class:`BasicPlayer`: A list of clan members.
        """
        return iter(BasicPlayer(mdata, self) for mdata in self._data.get('memberList', []))

    @property
    def members(self):
        """List[:class:`BasicPlayer`]: A list of clan members"""
        return list(self._members)

    @property
    def member_dict(self, attr='tag'):
        """Dict{attr: :class:`BasicPlayer`}: A dict of clan members by tag.

        Pass in an attribute of :class:`BasicPlayer` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self._members}

    def get_member(self, **attrs):
        """Returns the first :class:`BasicPlayer` that meets the attributes passed

        This will return the first member matching the attributes passed.

        An example of this looks like:

        .. code-block:: python3

            member = SearchClan.get_member(tag='tag')

        This search implements the :func:`coc.utils.get` function
        """
        return get(self._members, **attrs)

    async def get_detailed_members(self, cache=False, fetch=True):
        """Get detailed player information for every player in the clan.
        This will return an AsyncIterator of :class:`SearchPlayer`.

        Example
        --------

        .. code-block:: python3

            clan = client.get_clan('tag')

            async for player in clan.get_detailed_members(cache=True):
                print(player.name)

        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :return: AsyncIterator of :class:`SearchPlayer`
        """
        for n in self._members:
            yield self._http.client.get_player(n.tag, cache=cache, fetch=fetch)


class WarClan(Clan):
    """Represents a War Clan that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Clan`, and thus all attributes
    of :class:`Clan` can be expected to be present.

    Attributes
    -----------
    attack_count:
        :class:`int` - Number of attacks by clan this war
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
    __slots__ = ('_war', 'level',
                 'attack_count', 'stars', 'destruction', 'exp_earned',
                 'attacks_used', 'total_attacks', 'max_stars')

    def __init__(self, *, data, war):
        super(WarClan, self).__init__(data=data)

        self._war = war
        self.level = data.get('clanLevel')
        self.attack_count = data.get('attacks')
        self.stars = data.get('stars')
        self.destruction = data.get('destructionPercentage')
        self.exp_earned = data.get('expEarned')

        self.attacks_used = data.get('attacks')
        self.total_attacks = self._war.team_size * 2
        self.stars = data.get('stars')
        self.max_stars = self._war.team_size * 3
            
    @property
    def _members(self):
        """|iter|

        Returns an iterable of :class:`WarMember`: all clan members in war.
        """
        return iter(WarMember(data=mdata, war=self._war, clan=self)
                    for mdata in self._data.get('members', []))

    @property
    def members(self):
        """List[:class:`WarMember`]: List of all clan members in war"""
        return list(self._members)

    @property
    def members_dict(self, attr='tag'):
        """Dict{attr: :class:`WarMember`}: A dict of clan members in war by tag.

        Pass in an attribute of :class:`WarMember` to get that attribute as the key.
        """
        return {getattr(m, attr): m for m in self._members}

    @property
    def _attacks(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all attacks used by the clan this war.
        """
        return chain.from_iterable(iter(n._attacks for n in self._members))

    @property
    def attacks(self):
        """List[:class:`WarAttack`]: List of all attacks used this war."""
        return list(self._attacks)

    @property
    def _defenses(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: all defenses by clan members this war.
        """
        return chain.from_iterable(iter(n._defenses for n in self._members))

    @property
    def defenses(self):
        """List[:class:`WarAttack`]: List of all defenses by clan members this war."""
        return list(self._defenses)


class Player:
    """Represents the most stripped down version of a player.
    All other player classes inherit this.


    Attributes
    ------------
    tag:
        :class:`str` - The clan tag
    name:
        :class:`str` - The clan name
    """
    __slots__ = ('name', 'tag', '_data')

    def __init__(self, data):
        self._data = data
        self.name = data['name']
        self.tag = data.get('tag')

    def __str__(self):
        return self.name


class BasicPlayer(Player):
    """Represents a Basic Player that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Player`, and thus all attributes
    of :class:`Player` can be expected to be present.

    Attributes
    -----------
    clan:
        :class:`Basic Clan` - The clan the member belongs to. May be ``None``
    level:
        :class:`int` - The player level.
    trophies:
        :class:`int` - The player's trophy count.
    versus_trophies:
        :class:`int` - The player's versus trophy count.
    clan_rank:
        :class:`int` - The members clan rank
    clan_previous_rank
        :class:`int` - The members clan rank last season
    league_rank:
        :class:`int` - The player's current rank in their league for this season
    donations:
        :class:`int` - The members current donation count
    received:
        :class:`int` - The member's current donation received count
    attack_wins:
        :class:`int` - The players current attack wins for this season
    defense_wins:
        :class:`int` - The players current defense wins for this season
    """
    __slots__ = ('clan', 'level', 'trophies', 'versus_trophies',
                 'clan_rank', 'clan_previous_rank', 'league_rank', 'donations',
                 'received', 'attack_wins', 'defense_wins')

    def __init__(self, data, clan=None):
        super(BasicPlayer, self).__init__(data)

        self.clan = clan
        self.level = data.get('expLevel')
        self.trophies = data.get('trophies')
        self.versus_trophies = data.get('versusTrophies')
        self.clan_rank = data.get('clanRank')
        self.clan_previous_rank = data.get('clanRank')
        self.league_rank = data.get('rank')
        self.donations = data.get('donations')
        self.received = data.get('donationsReceived')
        self.attack_wins = data.get('attackWins')
        self.defense_wins = data.get('defenseWins')

        if not self.clan:
            cdata = data.get('clan')
            if cdata:
                self.clan = BasicClan(data=cdata)

    @property
    def league(self):
        """:class:`League`: The player's current league."""
        return try_enum(League, self._data.get('league'))

    @property
    def role(self):
        """:class:`str`: The members role in the clan - member, elder, etc."""
        role = self._data.get('role')
        if role == 'admin':
            return 'elder'
        return role


class WarMember(Player):
    """Represents a War Member that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits :class:`Player`, and thus all attributes
    of :class:`Player` can be expected to be present.


    Attributes
    -----------
    town_hall:
        :class:`int` - The members TH level
    map_position:
        :class:`int` - The members map position this war
    war:
        :class:`War` - The war this member belongs to
    clan:
        :class:`WarClan` - The war clan this member belongs to.
    """
    __slots__ = ('town_hall', 'map_position', 'war', 'clan')

    def __init__(self, data, war, clan):
        super(WarMember, self).__init__(data)

        self.war = war
        self.clan = clan

        self.town_hall = data.get('townHallLevel')
        self.map_position = data.get('mapPosition')

    @property
    def _attacks(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: the member's attacks this war"""
        return iter(WarAttack(data=adata, war=self.war, member=self)
                    for adata in self._data.get('attacks', []))

    @property
    def attacks(self):
        """List[:class:`WarAttack`]: The member's attacks this war. Could be an empty list"""
        return list(self._attacks)

    @property
    def _defenses(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: the member's defenses this war"""
        return filter(lambda o: o.defender_tag == self.tag, self.war.opponent._attacks)

    @property
    def defenses(self):
        """List[:class:`WarAttack`]: The member's defenses this war. Could be an empty list"""
        return list(self._defenses)

    @property
    def is_opponent(self):
        return self.clan.tag == self.war.opponent.tag


class SearchPlayer(BasicPlayer):
    """Represents a Searched Player that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    This class inherits both :class:`Player` and :class:`BasicPlayer`,
    and thus all attributes of these classes can be expected to be present

    Attributes
    -----------
    best_trophies:
        :class:`int` - The players top trophy count
    best_versus_trophies:
        :class:`int` - The players top versus trophy count
    war_stars:
        :class:`int` - The players war star count
    town_hall:
        :class:`int` - The players TH level
    builder_hall:
        :class:`int` - The players BH level
    versus_attacks_wins:
        :class:`int` - The players total BH wins
    """
    __slots__ = ('best_trophies', 'war_stars', 'town_hall',
                 'builder_hall', 'best_versus_trophies', 'versus_attacks_wins')

    def __init__(self, *, data):
        super(SearchPlayer, self).__init__(data=data)

        self.clan = try_enum(Clan, data.get('clan'))
        self.best_trophies = data.get('bestTrophies')
        self.war_stars = data.get('warStars')
        self.town_hall = data.get('townHallLevel')
        self.builder_hall = data.get('builderHallLevel')
        self.best_versus_trophies = data.get('bestVersusTrophies')
        self.versus_attacks_wins = data.get('versusBattleWins')

    @property
    def _achievements(self):
        """|iter|

        Returns an iterable of :class:`Achievement`: the player's achievements."""
        return iter(Achievement(data=adata, player=self)
                    for adata in self._data.get('achievements', []))

    @property
    def achievements(self):
        """List[:class:`Achievement`]: List of the player's achievements"""
        return list(self._achievements)

    @property
    def troops(self):
        """List[:class:`Troop`]: List of the player's troops"""
        return [Spell(data=sdata, player=self)
                for sdata in self._data.get('troops', [])]

    @property
    def heroes(self):
        """List[:class:`Hero`]: List of the player's heroes"""
        return [Hero(data=hdata, player=self)
                for hdata in self._data.get('heroes', [])]

    @property
    def spells(self):
        """List[:class:`Spell`]: List of the player's spells"""
        return [Spell(data=sdata, player=self)
                for sdata in self._data.get('spells', [])]
            
    @property
    def achievements_dict(self, attr='name'):
        """Dict{name: :class:`Achievement`}: A dict of achievements by name.

        Pass in an attribute of :class:`Achievement` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self._achievements}

    @property
    def troops_dict(self, attr='name'):
        """Dict{name: :class:`Troop`}: A dict of troops by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops}

    @property
    def heroes_dict(self, attr='name'):
        """Dict{name: :class:`Hero`}: A dict of heroes by name.

        Pass in an attribute of :class:`Hero` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.heroes}

    @property
    def spells_dict(self, attr='name'):
        """Dict{name: :class:`Spell`}: A dict of spells by name.

        Pass in an attribute of :class:`Spell` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.spells}


class BaseWar:
    """Represents the most basic Clash of Clans War

    Attributes
    -----------
    team_size:
        :class:`int` - The number of players per clan in war
    """
    __slots__ = ('team_size', '_data')

    def __init__(self, *, data):
        self._data = data
        self.team_size = data.get('teamSize')

    @property
    def clan(self):
        """:class:`WarClan`: The offensive clan"""
        clan = self._data.get('clan', {})
        if 'tag' in clan:
            # at the moment, if the clan is in notInWar, the API returns
            # 'clan' and 'opponent' as dicts containing only badge urls of
            # no specific clan. very strange

            return WarClan(data=clan, war=self)

    @property
    def opponent(self):
        """:class:`WarClan`: The opposition clan"""
        opponent = self._data.get('opponent', {})
        if 'tag' in opponent:
            # same issue as clan
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

    def __init__(self, *, data):
        self.result = data.get('result')
        self.end_time = try_enum(Timestamp, data.get('endTime'))
        super(WarLog, self).__init__(data=data)


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

    def __init__(self, *, data):
        self.state = data.get('state')
        self.preparation_start_time = try_enum(Timestamp, data.get('preparationStartTime'))
        self.start_time = try_enum(Timestamp, data.get('startTime'))
        self.end_time = try_enum(Timestamp, data.get('endTime'))

        super(CurrentWar, self).__init__(data=data)

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


class Achievement:
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

    __slots__ = ('player', 'name', 'stars', 'value', 'target',
                 'info', 'completion_info', 'village', '_data')

    def __str__(self):
        return self.name

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data['name']
        self.stars = data.get('stars')
        self.value = data['value']
        self.target = data['target']
        self.info = data['info']
        self.completion_info = data.get('completionInfo')
        self.village = data['village']

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the achievement belongs to the builder base"""
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the achievement belongs to the home base"""
        return self.village == 'home'

    @property
    def is_completed(self):
        """:class:`bool`: Indicates whether the achievement is completed (3 stars achieved)"""
        return self.stars == 3


class Troop:
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
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village', '_data')

    def __str__(self):
        return self.name

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the troop is the max level"""
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the troop belongs to the builder base"""
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the troop belongs to the home base"""
        return self.village == 'home'


class Hero:
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
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village', '_data')

    def __str__(self):
        return self.name

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the hero is the max level"""
        return self.level == self.max_level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the hero belongs to the builder base"""
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the hero belongs to the home base"""
        return self.village == 'home'


class Spell:
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
    __slots__ = ('player', 'name', 'level',
                 'max_level', 'village', '_data')

    def __str__(self):
        return self.name

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.name = data['name']
        self.level = data['level']
        self.max_level = data['maxLevel']
        self.village = data['village']

    @property
    def is_max(self):
        """:class:`bool`: Helper property to tell you if the spell is the max level"""
        return self.max_level == self.level

    @property
    def is_builder_base(self):
        """:class:`bool`: Helper property to tell you if the spell belongs to the builder base"""
        return self.village == 'builderBase'

    @property
    def is_home_base(self):
        """:class:`bool`: Helper property to tell you if the spell belongs to the home base"""
        return self.village == 'home'


class WarAttack:
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


class Location:
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
    """
    __slots__ = ('id', 'name', 'is_country', 'country_code', '_data')

    def __init__(self, *, data):
        self._data = data

        self.id = data.get('id')
        self.name = data.get('name')
        self.is_country = data.get('isCountry')
        self.country_code = data.get('countryCode')

    def __str__(self):
        return self.name


class League:
    """Represents a Clash of Clans League

    Attributes
    -----------
    id:
        :class:`str` - The league ID
    name:
        :class:`str` - The league name
    """
    __slots__ = ('id', 'name', '_data')

    def __init__(self, *, data):
        self._data = data

        self.id = data.get('id')
        self.name = data.get('name')

    @property
    def badge(self):
        """:class:`Badge`: The league's badge"""
        return try_enum(Badge, data=self._data.get('iconUrls'))

    def __str__(self):
        return self.name


class LeagueRankedPlayer(BasicPlayer):
    """Represents a Clash of Clans League Ranked Player.
    Note that league season information is available only for Legend League.

    This class inherits both :class:`Player` and :class:`BasicPlayer`,
    and thus all attributes of these classes can be expected to be present.


    Attributes
    -----------
    rank:
        :class:`int` - The players rank in their league for this season
    """
    def __init__(self, *, data):
        self.rank = data.get('rank')
        super(LeagueRankedPlayer, self).__init__(data=data)


class Season:
    """Represents a Clash of Clans Player's Season.

    rank: """
    __slots__ = ('rank', 'trophies', 'id')

    def __init__(self, *, data):
        self.rank = data.get('rank')
        self.trophies = data.get('trophies')
        self.id = data.get('id')


class LegendStatistics:
    """Represents the Legend Statistics for a player.

    Attributes
    -----------
    player:
        :class:`Player` - The player
    legend_trophies:
        :class:`int` - The player's legend trophies
    """
    __slots__ = ('player', 'legend_trophies', '_data')

    def __init__(self, *, data, player):
        self._data = data

        self.player = player
        self.legend_trophies = data['legendTrophies']

    @property
    def current_season(self):
        """:class:`int`: Legend trophies for this season."""
        return try_enum(Season, data=self._data.get('currentSeason'))

    @property
    def previous_season(self):
        """:class:`int`: Legend trophies for the previous season."""
        return try_enum(Season, data=self._data.get('previousSeason'))

    @property
    def best_season(self):
        """:class:`int`: Legend trophies for the player's best season."""
        return try_enum(Season, data=self._data.get('bestSeason'))


class Badge:
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
    __slots__ = ('small', 'medium', 'large', 'url', '_data')

    def __init__(self, *, data):
        # self._http = http
        self._data = data

        self.small = data.get('small')
        self.medium = data.get('medium')
        self.large = data.get('large')

        self.url = self.medium

    async def save(self, fp, size=None):
        """This funtion is a coroutine. Save this badge as a file-like object.

        :param fp: :class:`os.PathLike`
                    The filename to save the badge to
        :param size: Optional[:class:`str`] Either `small`, `medium` or `large`. The default is `medium`

        :raise HTTPException: Saving the badge failed

        :raise NotFound: The url was not found

        :return: :class:`int` The number of bytes written
        """
        sizes = {'small': self.small,
                 'medium': self.medium,
                 'large': self.large}

        if size and size in sizes.keys():
            url = sizes[size]
        else:
            url = self.medium

        # data = self._http.get_data_from_url(url)
        #
        # with open(fp, 'wb') as f:
        #     return f.write(data)


class Timestamp:
    """Represents a Clash of Clans Timestamp

    Attributes
    -----------
    time: :class:`str`: The raw timestamp string (ISO8601) as given by the API.
    """
    __slots__ = ('time', '_data')

    def __init__(self, *, data):
        self._data = data

        self.time = data

    @property
    def utc_timestamp(self):
        """:class:`datetime`: The timestamp as a UTC datetime object"""
        return from_timestamp(self.time)

    @property
    def now(self):
        """:class:`datetime`: The time in UTC now as a datetime object"""
        return datetime.utcnow()

    @property
    def seconds_until(self):
        """:class:`int`: Number of seconds until the timestamp. This may be negative."""
        delta = self.utc_timestamp - self.now
        return delta.total_seconds()


class LeaguePlayer:
    """Represents a Clash of Clans League Player

    Attributes
    -----------
    tag:
        :class:`str` - The player's tag
    name:
        :class:`str` - The player's name
    town_hall:
        :class:`int` - The player's town hall level"""

    __slots__ = ('tag', 'name', 'town_hall', '_data')

    def __str__(self):
        return self.name

    def __init__(self, *, data):
        self._data = data

        self.tag = data.get('tag')
        self.name = data.get('name')
        self.town_hall = data.get('townHallLevel')


class LeagueClan(BasicClan):
    """Represents a Clash of Clans League Clan

    This class inherits both :class:`Clan` and :class:`BasicClan`,
    and thus all attributes of these classes can be expected to be present.

    Attributes
    -----------

    """
    def __init__(self, *, data):
        super(LeagueClan, self).__init__(data=data)

    @property
    def _members(self):
        """|iter|

        Returns an iterable of :class:`LeaguePlayer`: all players participating in this league season"""
        return iter(LeaguePlayer(data=mdata) for mdata in self._data.get('members', []))

    @property
    def members(self):
        """List[:class:`LeaguePlayer`} A list of players participating in this league season"""
        return list(self._members)


class LeagueGroup:
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
        super(LeagueWar, self).__init__(data=data)


class LeagueWarLogEntry:
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
    """

    __slots__ = ('end_time', 'team_size', 'clan', 'enemy_stars',
                 'attack_count', 'stars', 'destruction', 'clan_level')

    def __init__(self, *, data):
        self.end_time = try_enum(Timestamp, data.get('endTime'))
        self.team_size = data.get('teamSize')
        self.clan = try_enum(Clan, data.get('clan'))
        try:
            self.enemy_stars = data['opponent']['stars']
        except KeyError:
            self.enemy_stars = None

        if self.clan:
            self.attack_count = self.clan._data.get('attacks')
            self.stars = self.clan._data.get('stars')
            self.destruction = self.clan._data.get('destructionPercentage')
            self.clan_level = self.clan._data.get('clanLevel')

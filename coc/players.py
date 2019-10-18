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

from collections import OrderedDict

from .miscmodels import EqualityComparable, try_enum, Achievement, Troop, Hero, Spell, League, Label
from .enums import HERO_ORDER, BUILDER_TROOPS_ORDER, HOME_TROOP_ORDER, SPELL_ORDER, LabelType
from .utils import maybe_sort


class Player(EqualityComparable):
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
        self.tag = data['tag']

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [
            ('tag', self.tag),
            ('name', self.name)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game
        """
        return 'https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}'.format(
            self.tag.strip('#')
        )


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
    exp_level:
        :class:`int` - The player's experience level.
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
    __slots__ = ('_http', 'clan', 'exp_level', 'trophies', 'versus_trophies',
                 'clan_rank', 'clan_previous_rank', 'league_rank', 'donations',
                 'received', 'attack_wins', 'defense_wins')

    def __init__(self, data, http, clan=None):
        super(BasicPlayer, self).__init__(data)
        self._http = http

        self.clan = clan
        self.exp_level = data.get('expLevel')
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
                from .clans import BasicClan  # hack because circular imports
                self.clan = BasicClan(data=cdata, http=http)

    @property
    def league(self, default=None):
        """:class:`League`: The player's current league.

        Pass in a default value to return if no league is found (the player is 'Unranked').
        """
        return try_enum(League, self._data.get('league'), default=default, http=self._http)

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

        self.town_hall = data.get('townhallLevel')
        self.map_position = data.get('mapPosition')

    def _get_attacks(self):
        from .wars import WarAttack  # hack because circular imports

        return iter(WarAttack(data=adata, war=self.war, member=self)
                    for adata in self._data.get('attacks', []))

    @property
    def iterattacks(self, sort: bool = True):
        """|iter|

        Returns an iterable of :class:`WarAttack`: the member's attacks this war
        """
        return maybe_sort(self._get_attacks(), sort, itr=True)

    @property
    def attacks(self, sort: bool = True):
        """List[:class:`WarAttack`]: The member's attacks this war. Could be an empty list
        """
        return maybe_sort(self._get_attacks(), sort)

    @property
    def iterdefenses(self):
        """|iter|

        Returns an iterable of :class:`WarAttack`: the member's defenses this war
        """
        # TODO: efficient way of doing this
        return filter(lambda o: o.defender_tag == self.tag, self.war.opponent.iterattacks)

    @property
    def defenses(self):
        """List[:class:`WarAttack`]: The member's defenses this war. Could be an empty list
        """
        return list(self.iterattacks)

    @property
    def is_opponent(self):
        """Bool: Indicates whether the member is from the opponent clan or not."""
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

    def __init__(self, *, data, http):
        super(SearchPlayer, self).__init__(data=data, http=http)

        from .clans import Clan  # hack because circular imports

        self.clan = try_enum(Clan, data.get('clan'), http=http)
        self.best_trophies = data.get('bestTrophies')
        self.war_stars = data.get('warStars')
        self.town_hall = data.get('townHallLevel')
        self.builder_hall = data.get('builderHallLevel', 0)
        self.best_versus_trophies = data.get('bestVersusTrophies')
        self.versus_attacks_wins = data.get('versusBattleWins')

    @property
    def iterlabels(self):
        """|iter|

        Returns an iterable of :class:`Label`: the player's labels.
        """
        return iter(
            Label(data=ldata, http=self._http, label_type=LabelType.player) for ldata in self._data.get('labels', [])
        )

    @property
    def labels(self):
        """List[:class:`Label`]: List of the player's labels."""
        return list(self.iterlabels)

    @property
    def iterachievements(self):
        """|iter|

        Returns an iterable of :class:`Achievement`: the player's achievements.
        """
        return iter(Achievement(data=adata, player=self)
                    for adata in self._data.get('achievements', []))

    @property
    def achievements(self):
        """List[:class:`Achievement`]: List of the player's achievements
        """
        return list(self.iterachievements)

    @property
    def troops(self):
        """List[:class:`Troop`]: List of the player's troops
        """
        return [Troop(data=sdata, player=self)
                for sdata in self._data.get('troops', [])]

    @property
    def heroes(self):
        """List[:class:`Hero`]: List of the player's heroes
        """
        return [Hero(data=hdata, player=self)
                for hdata in self._data.get('heroes', [])]

    @property
    def spells(self):
        """List[:class:`Spell`]: List of the player's spells
        """
        return [Spell(data=sdata, player=self)
                for sdata in self._data.get('spells', [])]

    @property
    def achievements_dict(self, attr='name'):
        """:class:`dict` - {name: :class:`Achievement`} A dict of achievements by name.

        Pass in an attribute of :class:`Achievement` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.iterachievements}

    @property
    def home_troops_dict(self, attr='name'):
        """:class:`dict` - {name: :class:`Troop`}: A dict of home base troops by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops if m.is_home_base}

    @property
    def builder_troops_dict(self, attr='name'):
        """:class:`dict` - {name: :class:`Troop`}: A dict of builder base troops by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops if m.is_builder_base}

    @property
    def heroes_dict(self, attr='name'):
        """:class:`dict` - {name: :class:`Hero`}: A dict of heroes by name.

        Pass in an attribute of :class:`Hero` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.heroes}

    @property
    def spells_dict(self, attr='name'):
        """:class:`dict` - {name: :class:`Spell`}: A dict of spells by name.

        Pass in an attribute of :class:`Spell` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.spells}

    @property
    def ordered_home_troops(self):
        """:class:`collections.OrderedDict` - An ordered dict of troops by name.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(HOME_TROOP_ORDER)}
        return OrderedDict(sorted(self.home_troops_dict.items(), key=lambda i: key_order.get(i[0])))

    @property
    def ordered_builder_troops(self):
        """:class:`collections.OrderedDict` - An ordered dict of home base troops by name.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(BUILDER_TROOPS_ORDER)}
        return OrderedDict(sorted(self.builder_troops_dict.items(),
                                  key=lambda i: key_order.get(i[0])))

    @property
    def ordered_spells(self):
        """:class:`collections.OrderedDict` - An ordered dict of spells by name.

        This will return spells in the order found in both spell factory and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(SPELL_ORDER)}
        return OrderedDict(sorted(self.spells_dict.items(), key=lambda i: key_order.get(i[0])))

    @property
    def ordered_heroes(self):
        """:class:`collections.OrderedDict` - An ordered dict of heroes by name.

        This will return heroes in the order found in the labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(HERO_ORDER)}
        return OrderedDict(sorted(self.heroes_dict.items(), key=lambda i: key_order.get(i[0])))


class LeaguePlayer(EqualityComparable):
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

    def __repr__(self):
        attrs = [
            ('tag', self.tag),
            ('name', self.name),
            ('town_hall', self.town_hall)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    def __init__(self, *, data):
        self._data = data

        self.tag = data.get('tag')
        self.name = data.get('name')
        self.town_hall = data.get('townHallLevel')

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game"""
        return 'https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}'.format(
            self.tag.strip('#')
        )


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
    __slots__ = 'rank'

    def __init__(self, *, data, http):
        self.rank = data.get('rank')
        super(LeagueRankedPlayer, self).__init__(data=data, http=http)

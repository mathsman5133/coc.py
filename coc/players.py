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

from .miscmodels import EqualityComparable, try_enum, Achievement, Troop, Hero, Spell, Label, League, LegendStatistics
from .enums import (
    Role,
    HERO_ORDER,
    BUILDER_TROOPS_ORDER,
    HOME_TROOP_ORDER,
    SPELL_ORDER,
    SIEGE_MACHINE_ORDER,
    UNRANKED_LEAGUE_DATA,
)
from .utils import maybe_sort, peek_at_generator


class ClanMember:
    __slots__ = (
        "_client",
        "_clan_tag",
        "name",
        "tag",
        "role",
        "exp_level",
        "league",
        "trophies",
        "versus_trophies",
        "clan_rank",
        "clan_previous_rank",
        "donations",
        "received",
    )

    def __init__(self, *, data, client):
        self._client = client

    def _from_data(self, data):
        data_get = data.get
        # always available
        self.name = data_get("name")
        self.tag = data_get("tag")

        self.exp_level = data_get("expLevel")
        self.trophies = data_get("trophies")
        self.versus_trophies = data_get("versusTrophies")
        self.clan_rank = data_get("clanRank")
        self.clan_previous_rank = data_get("clanRank")
        self.donations = data_get("donations")
        self.received = data_get("donationsReceived")

        clan_data = data_get("clan")
        if clan_data:
            self._client._update_clan(clan_data)
            self._clan_tag = clan_data["tag"]

        self.league = try_enum(League, data_get("league") or UNRANKED_LEAGUE_DATA, client=self._client)
        self.role = Role(data_get("role"))


class Player(ClanMember):
    __slots__ = ClanMember.__slots__ + (
        "attack_wins",
        "defense_wins",
        "best_trophies",
        "war_stars",
        "town_hall",
        "town_hall_weapon" "builder_hall",
        "best_versus_trophies",
        "versus_attack_wins",
        "legend_statistics",
        "_achievements",
        "_heroes",
        "_labels",
        "_spells",
        "_troops",
        "__iter_achievements",
        "__iter_heroes",
        "__iter_labels",
        "__iter_spells",
        "__iter_troops",
    )

    def __init__(self, *, data, client):
        super().__init__(data=data, client=client)
        self._client = client

        self._achievements = {}
        self._heroes = {}
        self._labels = []
        self._spells = []
        self._troops = []

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = (("tag", self.tag), ("name", self.name))
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(cls, data):
        data_get = data.get

        # always available
        self.name = data_get("name")
        self.tag = data_get("tag")

        clan_data = data_get("clan")
        if clan_data:
            self._client._update_clan(clan_data)
            self._clan_tag = clan_data["tag"]

        self.league = try_enum(League, data_get("league") or UNRANKED_LEAGUE_DATA, client=self._client)
        self.role = Role(data_get("role"))
        self.best_trophies = data_get("bestTrophies")
        self.war_stars = data_get("warStars")
        self.town_hall = data_get("townHallLevel")
        self.builder_hall = data_get("builderHallLevel", 0)
        self.best_versus_trophies = data_get("bestVersusTrophies")
        self.versus_attack_wins = data_get("versusBattleWins")
        self.legend_statistics = try_enum(LegendStatistics, data_get("legendStatistics"), player_tag=self.tag)

        self.__iter_labels = (Label(data=ldata, client=self._client) for ldata in data_get("labels", []))
        self.__iter_achievements = (Achievement(data=adata, player=self) for adata in data_get("achievements", []))
        self.__iter_troops = (Troop(data=sdata, player=self) for sdata in data_get.get("troops", []))
        self.__iter_heroes = (Hero(data=hdata, player=self) for hdata in data_get("heroes", []))
        self.__iter_spells = (Spell(data=sdata, player=self) for sdata in data_get("spells", []))

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game"""
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))

    @property
    def clan(self):
        """Optional[:class:`Clan`]: The player's clan. If the player is clanless, this will be ``None``."""
        return self._clan_tag and self._client.get_clan(self._clan_tag)

    @property
    def labels(self):
        """List[:class:`Label`]: A :class:`List` of :class:`Label` that the player has."""
        iter_labels = peek_at_generator(self.__iter_labels)
        if iter_labels:
            self._labels = list(iter_labels)

        return self._labels

    @property
    def achievements(self):
        """List[:class:`Achievement`]: A :class:`List` of the player's :class:`Achievement`s."""
        iter_achievements = peek_at_generator(self.__iter_achievements)
        if iter_achievements:
            self._achievements = {a.name: a for a in iter_achievements}

        return list(self._achievements.values())

    def get_achievement(self, name):
        """Returns an achievement with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of an achievement as found in-game.

        Returns
        --------
        Optional[:class:`Achievement`]
            The returned achievement or ``None`` if not found.
        """
        try:
            return self._achievements[name]
        except KeyError:
            return None

    @property
    def troops(self):
        """List[:class:`Troop`]: A :class:`List` of the player's :class:`Troop`s.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        iter_troops = peek_at_generator(self.__iter_troops)
        if iter_troops:
            self._troops = list(iter_troops)
        return self._troops

    @property
    def home_troops(self):
        """List[:class:`Troop`]: A :class:`List` of the player's home-base :class:`Troop`s.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        order = {k: v for v, k in enumerate(HOME_TROOP_ORDER)}
        troops = (t for t in self.troops if t.is_home_base)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @property
    def builder_troops(self):
        """List[:class:`Troop`]: A :class:`List` of the player's builder-base :class:`Troop`s.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        order = {k: v for v, k in enumerate(BUILDER_TROOPS_ORDER)}
        troops = (t for t in self.troops if t.is_home_base)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @property
    def siege_machines(self):
        """List[:class:`Troop`]: A :class:`List` of the player's siege-machine :class:`Troop`s.

        This will return siege machines in the order found in both barracks and labatory in-game.
        """
        order = {k: v for v, k in enumerate(SIEGE_MACHINE_ORDER)}
        troops = (t for t in self.troops if t.name in SIEGE_MACHINE_ORDER)
        return list(sorted(troops, key=lambda t: order.get(t.name)))

    @property
    def heroes(self):
        """List[:class:`Hero`]: A :class:`List` of the player's :class:`Hero`es.

        This will return heroes in the order found in the store and labatory in-game.
        """
        iter_heroes = peek_at_generator(self.__iter_heroes)
        if iter_heroes:
            self._heroes = {h.name: h for h in iter_heroes}

        order = {k: v for v, k in enumerate(HERO_ORDER)}
        return list(sorted(self._heroes.values(), key=lambda h: order.get(h.name, 0)))

    def get_hero(self, name):
        """Returns a hero with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a hero as found in-game.

        Returns
        --------
        Optional[:class:`Hero`]
            The returned hero or ``None`` if not found.
        """
        try:
            return self._heroes[name]
        except KeyError:
            return None

    @property
    def spells(self):
        """List[:class:`Spell`]: A :class:`List` of the player's :class:`Spell`s ordered as they appear in-game.

        This will return spells in the order found in both spell factory and labatory in-game.
        """
        iter_spells = peek_at_generator(self.__iter_spells)
        if iter_spells:
            self._spells = list(iter_spells)

        order = {k: v for v, k in enumerate(SPELL_ORDER)}
        return list(sorted(self._spells, key=lambda s: order.get(s.name)))


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

    __slots__ = ("name", "tag", "_data")

    def __init__(self, data):
        self._data = data
        self.name = data["name"]
        self.tag = data["tag"]

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("tag", self.tag), ("name", self.name)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game
        """
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))


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

    __slots__ = (
        "_http",
        "clan",
        "exp_level",
        "trophies",
        "versus_trophies",
        "clan_rank",
        "clan_previous_rank",
        "league_rank",
        "donations",
        "received",
        "attack_wins",
        "defense_wins",
    )

    def __init__(self, data, http, clan=None):
        # pylint: disable=cyclic-import, import-outside-toplevel
        super(BasicPlayer, self).__init__(data)
        self._http = http

        self.clan = clan
        self.exp_level = data.get("expLevel")
        self.trophies = data.get("trophies")
        self.versus_trophies = data.get("versusTrophies")
        self.clan_rank = data.get("clanRank")
        self.clan_previous_rank = data.get("clanRank")
        self.league_rank = data.get("rank")
        self.donations = data.get("donations")
        self.received = data.get("donationsReceived")
        self.attack_wins = data.get("attackWins")
        self.defense_wins = data.get("defenseWins")

        if not self.clan:
            cdata = data.get("clan")
            if cdata:
                from .clans import BasicClan  # hack because circular imports

                self.clan = BasicClan(data=cdata, http=http)

    @property
    def league(self):
        """:class:`League`: The player's current league."""
        data = self._data.get("league") or UNRANKED_LEAGUE_DATA
        return try_enum(League, data, http=self._http)

    @property
    def role(self):
        """:class:`str`: The members role in the clan - member, elder, etc."""
        return Role(self._data.get("role"))


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

    __slots__ = ("town_hall", "map_position", "war", "clan")

    def __init__(self, data, war, clan):
        super(WarMember, self).__init__(data)

        self.war = war
        self.clan = clan

        self.town_hall = data.get("townhallLevel")
        self.map_position = data.get("mapPosition")

    def _get_attacks(self):
        # pylint: disable=import-outside-toplevel
        from .wars import WarAttack  # hack because circular imports

        return iter(WarAttack(data=adata, war=self.war, member=self) for adata in self._data.get("attacks", []))

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
        return list(self.iterdefenses)

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
    versus_attack_wins:
        :class:`int` - The players total BH wins
    legend_statistics:
        Optional[:class:`LegendStatistics`] - the player's legend statistics, if applicable.
    """

    __slots__ = (
        "best_trophies",
        "war_stars",
        "town_hall",
        "builder_hall",
        "best_versus_trophies",
        "versus_attack_wins",
        "legend_statistics",
    )

    def __init__(self, *, data, http):
        # pylint: disable=import-outside-toplevel
        super(SearchPlayer, self).__init__(data=data, http=http)

        from .clans import Clan  # hack because circular imports

        self.clan = try_enum(Clan, data.get("clan"), http=http)
        self.best_trophies = data.get("bestTrophies")
        self.war_stars = data.get("warStars")
        self.town_hall = data.get("townHallLevel")
        self.builder_hall = data.get("builderHallLevel", 0)
        self.best_versus_trophies = data.get("bestVersusTrophies")
        self.versus_attack_wins = data.get("versusBattleWins")
        self.legend_statistics = try_enum(LegendStatistics, data.get("legendStatistics"), player=self)

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
    def iterachievements(self):
        """|iter|

        Returns an iterable of :class:`Achievement`: the player's achievements.
        """
        return iter(Achievement(data=adata, player=self) for adata in self._data.get("achievements", []))

    @property
    def achievements(self):
        """List[:class:`Achievement`]: List of the player's achievements
        """
        return list(self.iterachievements)

    @property
    def troops(self):
        """List[:class:`Troop`]: List of the player's troops
        """
        return [Troop(data=sdata, player=self) for sdata in self._data.get("troops", [])]

    @property
    def heroes(self):
        """List[:class:`Hero`]: List of the player's heroes
        """
        return [Hero(data=hdata, player=self) for hdata in self._data.get("heroes", [])]

    @property
    def spells(self):
        """List[:class:`Spell`]: List of the player's spells
        """
        return [Spell(data=sdata, player=self) for sdata in self._data.get("spells", [])]

    @property
    def achievements_dict(self, attr="name"):
        """:class:`dict` - {name: :class:`Achievement`} A dict of achievements by name.

        Pass in an attribute of :class:`Achievement` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.iterachievements}

    @property
    def home_troops_dict(self, attr="name"):
        """:class:`dict` - {name: :class:`Troop`}: A dict of home base troops by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops if m.is_home_base}

    @property
    def builder_troops_dict(self, attr="name"):
        """:class:`dict` - ``{name: :class:`Troop`}``: A dict of builder base troops by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops if m.is_builder_base}

    @property
    def siege_machines_dict(self, attr="name"):
        """:class:`dict` - ``{name: :class:`Troop`}``: A dict of siege machines by name.

        Pass in an attribute of :class:`Troop` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.troops if m.name in SIEGE_MACHINE_ORDER}

    @property
    def heroes_dict(self, attr="name"):
        """:class:`dict` - ``{name: :class:`Hero`}``: A dict of heroes by name.

        Pass in an attribute of :class:`Hero` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.heroes}

    @property
    def spells_dict(self, attr="name"):
        """:class:`dict` - ``{name: :class:`Spell`}``: A dict of spells by name.

        Pass in an attribute of :class:`Spell` to get that attribute as the key
        """
        return {getattr(m, attr): m for m in self.spells}

    def get_ordered_troops(self, valid_troops):
        """Get an ordered dict of a player's troops against a predefined list of troops.

        The most common use of this will be passing in one of the following:


        - ``coc.ELIXIR_TROOP_ORDER``

        - ``coc.DARK_ELIXIR_TROOP_ORDER``

        - ``coc.SIEGE_MACHINE_ORDER``

        - ``coc.HOME_TROOP_ORDER``

        - ``coc.BUILDER_TROOPS_ORDER``


        Which will yield an ordered dict of the player's troops, ordered as found in both barracks and labatory in-game.

        Example
        ---------

        .. code-block:: python3

            # to get an ordered dict of a player's elixir troops.
            import coc

            player = client.get_player(...)
            elixir_troops = player.get_ordered_troops(coc.ELIXIR_TROOP_ORDER)

            for troop_name, troop in elixir_troops.items():
               ...

        Returns
        --------
        :class:`collections.OrderedDict` - An ordered dict of troops by name.
        """
        troops_dict = {t.name: t for t in self.troops if t.name in set(valid_troops)}
        key_order = {k: v for v, k in enumerate(valid_troops)}
        return OrderedDict(sorted(troops_dict.items(), key=lambda i: key_order.get(i[0])))

    @property
    def ordered_home_troops(self):
        """:class:`collections.OrderedDict` - An ordered dict of troops by name.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(HOME_TROOP_ORDER)}
        return OrderedDict(sorted(self.home_troops_dict.items(), key=lambda i: key_order.get(i[0])))

    @property
    def ordered_builder_troops(self):
        """:class:`collections.OrderedDict` - An ordered dict of builder base troops by name.

        This will return troops in the order found in both barracks and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(BUILDER_TROOPS_ORDER)}
        return OrderedDict(sorted(self.builder_troops_dict.items(), key=lambda i: key_order.get(i[0])))

    @property
    def ordered_siege_machines(self):
        """:class:`collections.OrderedDict` - An ordered dict of siege machines by name.

        This will return siege machines in the order found in both barracks and labatory in-game.
        """
        key_order = {k: v for v, k in enumerate(SIEGE_MACHINE_ORDER)}
        return OrderedDict(sorted(self.siege_machines_dict.items(), key=lambda i: key_order.get(i[0])))

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

    __slots__ = ("tag", "name", "town_hall", "_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("tag", self.tag), ("name", self.name), ("town_hall", self.town_hall)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data):
        self._data = data

        self.tag = data.get("tag")
        self.name = data.get("name")
        self.town_hall = data.get("townHallLevel")

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game"""
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))


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

    __slots__ = ("rank",)

    def __init__(self, *, data, http):
        self.rank = data.get("rank")
        super(LeagueRankedPlayer, self).__init__(data=data, http=http)

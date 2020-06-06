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
from .miscmodels import try_enum, Achievement, Troop, Hero, Spell, Label, League, LegendStatistics
from .enums import (
    Role,
    HERO_ORDER,
    BUILDER_TROOPS_ORDER,
    HOME_TROOP_ORDER,
    SPELL_ORDER,
    SIEGE_MACHINE_ORDER,
    UNRANKED_LEAGUE_DATA,
    ACHIEVEMENT_ORDER,
    SUPER_TROOP_ORDER,
)
from .utils import peek_at_generator
from .abc import BaseClan, BasePlayer
from .player_clan import PlayerClan


class ClanMember(BasePlayer):
    """
    Optional[:class:`Clan`]: The player's clan. If the player is clanless, this will be ``None``.
    """

    __slots__ = (
        "_client",
        "clan",
        "role",
        "exp_level",
        "league",
        "trophies",
        "versus_trophies",
        "clan_rank",
        "clan_previous_rank",
        "donations",
        "received",
        "clan_cls",
        "league_cls",
    )

    def __init__(self, *, data, client, **kwargs):
        super().__init__(data=data, client=client)
        self._client = client
        self.clan_cls = PlayerClan
        self.league_cls = League
        self._from_data(data)

    def _from_data(self, data):
        data_get = data.get

        self.exp_level = data_get("expLevel")
        self.trophies = data_get("trophies")
        self.versus_trophies = data_get("versusTrophies")
        self.clan_rank = data_get("clanRank")
        self.clan_previous_rank = data_get("clanPreviousRank")
        self.donations = data_get("donations")
        self.received = data_get("donationsReceived")

        self.clan = try_enum(self.clan_cls, data=data_get("clan"), client=self._client)
        self.league = try_enum(self.league_cls, data=data_get("league") or UNRANKED_LEAGUE_DATA, client=self._client)
        self.role = try_enum(Role, value=data_get("role"))


class Player(ClanMember):
    __slots__ = (
        "clan",
        "attack_wins",
        "defense_wins",
        "best_trophies",
        "war_stars",
        "town_hall",
        "town_hall_weapon",
        "builder_hall",
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
        "achievement_cls",
        "hero_cls",
        "label_cls",
        "spell_cls",
        "troop_cls",
    )

    def __init__(self, *, data, client, **kwargs):
        self._client = client

        self._achievements = {}
        self._heroes = {}
        self._labels = []
        self._spells = []
        self._troops = []

        self.achievement_cls = Achievement
        self.hero_cls = Hero
        self.label_cls = Label
        self.spell_cls = Spell
        self.troop_cls = Troop

        super().__init__(data=data, client=client)

    def _from_data(self, data):
        super()._from_data(data)
        data_get = data.get

        self.best_trophies = data_get("bestTrophies")
        self.war_stars = data_get("warStars")
        self.town_hall = data_get("townHallLevel")
        self.town_hall_weapon = data_get("townHallWeaponLevel")
        self.builder_hall = data_get("builderHallLevel", 0)
        self.best_versus_trophies = data_get("bestVersusTrophies")
        self.versus_attack_wins = data_get("versusBattleWins")
        self.legend_statistics = try_enum(LegendStatistics, data=data_get("legendStatistics"))

        label_cls = self.label_cls
        achievement_cls = self.achievement_cls
        troop_cls = self.troop_cls
        hero_cls = self.hero_cls
        spell_cls = self.spell_cls

        self.__iter_labels = (label_cls(data=ldata, client=self._client) for ldata in data_get("labels", []))
        self.__iter_achievements = (achievement_cls(data=adata) for adata in data_get("achievements", []))
        self.__iter_troops = (troop_cls(data=sdata) for sdata in data_get("troops", []))
        self.__iter_heroes = (hero_cls(data=hdata) for hdata in data_get("heroes", []))
        self.__iter_spells = (spell_cls(data=sdata) for sdata in data_get("spells", []))

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
        # at the time of writing, the API presents achievements in the order
        # added to the game which doesn't match in-game order.
        dict_achievements = self._achievements
        if dict_achievements:
            return list(dict_achievements.values())

        achievement_dict = {a.name: a for a in self.__iter_achievements}
        sorted_achievements = {}
        for name in ACHIEVEMENT_ORDER:
            try:
                sorted_achievements[name] = achievement_dict[name]
            except KeyError:
                continue

        self._achievements = sorted_achievements
        return list(sorted_achievements.values())

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
        dict_achievements = self._achievements
        if not dict_achievements:
            _ = self.achievements
            dict_achievements = self._achievements

        try:
            return dict_achievements[name]
        except KeyError:
            return None

    @property
    def troops(self):
        """List[:class:`Troop`]: A :class:`List` of the player's :class:`Troop`s.

        Troops are **not** ordered in this attribute. Use either :attr:`Player.home_troops`
        or :attr:`Player.builder_troops` if you want an ordered list.
        """
        list_troops = self._troops
        if list_troops:
            return list_troops

        list_troops = self._troops = list(t for t in self.__iter_troops if t.name not in SUPER_TROOP_ORDER)
        return list_troops

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
        troops = (t for t in self.troops if t.is_builder_base)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @property
    def siege_machines(self):
        """List[:class:`Troop`]: A :class:`List` of the player's siege-machine :class:`Troop`s.

        This will return siege machines in the order found in both barracks and labatory in-game.
        """
        order = {k: v for v, k in enumerate(SIEGE_MACHINE_ORDER)}
        troops = (t for t in self.troops if t.name in SIEGE_MACHINE_ORDER)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @property
    def heroes(self):
        """List[:class:`Hero`]: A :class:`List` of the player's :class:`Hero`es.

        This will return heroes in the order found in the store and labatory in-game.
        """
        dict_heroes = self._heroes
        if dict_heroes:
            return list(dict_heroes.values())

        heroes_dict = {h.name: h for h in self.__iter_heroes}
        sorted_heroes = {}
        for name in HERO_ORDER:
            # have to do it this way because it's less expensive than removing None's if they don't have a troop.
            try:
                sorted_heroes[name] = heroes_dict[name]
            except KeyError:
                continue

        self._heroes = sorted_heroes
        return list(sorted_heroes.values())

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
        dict_heroes = self._heroes
        if not dict_heroes:
            dict_heroes = self._heroes = {h.name: h for h in self.__iter_heroes}

        try:
            return dict_heroes[name]
        except KeyError:
            return None

    @property
    def spells(self):
        """List[:class:`Spell`]: A :class:`List` of the player's :class:`Spell`s ordered as they appear in-game.

        This will return spells in the order found in both spell factory and labatory in-game.
        """
        list_spells = self._spells
        if not list_spells:
            list_spells = self._spells = list(self.__iter_spells)

        order = {k: v for v, k in enumerate(SPELL_ORDER)}
        return list(sorted(list_spells, key=lambda s: order.get(s.name)))


#
# class LeagueRankedPlayer(BasicPlayer):
#     """Represents a Clash of Clans League Ranked Player.
#     Note that league season information is available only for Legend League.
#
#     This class inherits both :class:`Player` and :class:`BasicPlayer`,
#     and thus all attributes of these classes can be expected to be present.
#
#
#     Attributes
#     -----------
#     rank:
#         :class:`int` - The players rank in their league for this season
#     """
#
#     __slots__ = ("rank",)
#
#     def __init__(self, *, data, http):
#         self.rank = data.get("rank")
#         super(LeagueRankedPlayer, self).__init__(data=data, http=http)

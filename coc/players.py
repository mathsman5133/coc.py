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
from typing import Optional, List, TYPE_CHECKING


from .miscmodels import BaseLeague, PlayerHouseElement, try_enum, Achievement, Label, League, LegendStatistics
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
    PETS_ORDER,
    EQUIPMENT,
)
from .abc import BasePlayer
from .hero import Hero, Equipment, Pet
from .player_clan import PlayerClan
from .spell import Spell
from .troop import Troop
from .utils import cached_property


if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .clans import Clan  # noqa


class ClanMember(BasePlayer):
    """Represents a Clash of Clans Clan Member.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    clan: Optional[:class:`Clan`]
        The player's clan. If the player is clanless, this will be ``None``.
    role: :class:`Role`
        The member's role in a clan. To get a string as rendered in-game, do ``str(member.role)``.
    exp_level: :class:`int`
        The member's experience level.
    league: :class:`League`
        The member's current league.
    builder_base_league: :class:`BaseLeague`
        The member's current builder base league.
    trophies: :class:`int`
        The member's trophy count.
    builder_base_trophies: :class:`int`
        The member's builder base trophy count.
    town_hall: :class:`int`
        The player's town hall level. In case the player hasn't logged in since 2019, this will be `0`.
    clan_rank: :class:`int`
        The member's rank in the clan.
    clan_previous_rank: :class:`int`
        The member's rank before the last leaderboard change
        (ie if Bob overtakes Jim in trophies, and they switch ranks on the leaderboard,
        and you want to find out their previous rankings, this will help.).
    builder_base_rank: :class:`int`
        The member's rank in the clan based on builder base trophies.
    donations: :class:`int`
        The member's donation count for this season.
    received: :class:`int`
        The member's donations received count for this season.
    clan_cls: :class:`coc.Clan`
        The class to use to create the :attr:`ClanMember.clan` attribute.
        Ensure any overriding of this inherits from :class:`coc.Clan` or :class:`coc.PlayerClan`.
    league_cls: :class:`coc.League`
        The class to use to create the :attr:`ClanMember.league` attribute.
        Ensure any overriding of this inherits from :class:`coc.League`.
    builder_base_league_cls: :class:`coc.League`
        The class to use to create the :attr:`ClanMember.builder_base_league` attribute.
        Ensure any overriding of this inherits from :class:`coc.BaseLeague`.
    """

    __slots__ = (
        "_client",
        "clan",
        "role",
        "exp_level",
        "league",
        "builder_base_league",
        "trophies",
        "builder_base_trophies",
        "clan_rank",
        "clan_previous_rank",
        "builder_base_rank",
        "donations",
        "received",
        "clan_cls",
        "league_cls",
        "builder_base_league_cls",
        "_player_house_elements",
        "player_house_element_cls",
        "_iter_player_house_elements",
        "_cs_player_house_elements",
        "town_hall",
    )

    def __init__(self, *, data, client, clan=None, **_):
        super().__init__(data=data, client=client)
        self._client = client
        self.clan_cls = PlayerClan
        self.league_cls = League
        self.builder_base_league_cls = BaseLeague
        self.player_house_element_cls = PlayerHouseElement

        self._from_data(data)
        if clan:
            self.clan = clan

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.exp_level: int = data_get("expLevel")
        self.trophies: int = data_get("trophies")
        self.builder_base_trophies: int = data_get("builderBaseTrophies")
        self.clan_rank: int = data_get("clanRank")
        self.clan_previous_rank: int = data_get("previousClanRank")
        self.builder_base_rank: int = data.get("builderBaseRank")
        self.donations: int = data_get("donations")
        self.received: int = data_get("donationsReceived")
        player_house_element_cls = self.player_house_element_cls
        self.clan = try_enum(self.clan_cls, data=data_get("clan"), client=self._client)
        self.league = try_enum(self.league_cls, data=data_get("league") or UNRANKED_LEAGUE_DATA, client=self._client)
        self.builder_base_league = try_enum(self.builder_base_league_cls,
                                            data=data_get("builderBaseLeague") or UNRANKED_LEAGUE_DATA,
                                            client=self._client)
        self.role = data_get("role") and Role(value=data["role"])
        self.town_hall: int = data_get("townHallLevel")
        self._iter_player_house_elements = (player_house_element_cls(data=adata)
                                            for adata in data_get("playerHouse", {}).get("elements", []))

    async def get_detailed_clan(self) -> Optional["Clan"]:
        """Get clan details for the player's clan. If the player's clan is ``None``,this will return ``None``.

        Example
        ---------

        .. code-block:: python3

            player = await client.get_player('tag')
            clan = await player.get_detailed_clan()
        """
        return self.clan and await self._client.get_clan(self.clan.tag)

    @cached_property("_cs_player_house_elements")
    def player_house_elements(self) -> List[PlayerHouseElement]:
        """List[:class:`PlayerHouseElement`]: A :class:`List` of :class:`PlayerHouseElement`\s that the player has."""
        return list(self._iter_player_house_elements)


class RankedPlayer(ClanMember):
    """
    Represents a leaderboard-ranked player.

    Attributes
    ----------
    attack_wins: :class:`int`
        The player's number of attack wins. If retrieving info for builder base leader-boards, this will be ``None``.
    defense_wins: :class:`int`
        The player's number of defense wins. If retrieving info for builder base leader-boards, this will be ``None``.
    builder_base_trophies: :class:`int`
        The player's builder base trophy count. If retrieving info for regular leader-boards, this will be ``None``.
    rank: :class:`int`
        The player's rank in the clan leaderboard.
    previous_rank: :class:`int`
        The member's rank before the last clan leaderboard change
        (ie if Bob overtakes Jim in trophies, and they switch ranks on the leaderboard,
        and you want to find out their previous rankings, this will help.).
    """

    __slots__ = ("attack_wins", "defense_wins", "builder_base_trophies", "rank", "previous_rank")

    def _from_data(self, data: dict) -> None:
        super()._from_data(data)

        data_get = data.get
        self.attack_wins: int = data_get("attackWins")
        self.defense_wins: int = data_get("defenseWins")
        self.builder_base_trophies: int = data_get("builderBaseTrophies")
        self.rank: int = data_get("rank")
        self.previous_rank: int = data_get("previousRank")


class Player(ClanMember):
    """
    Represents a Clash of Clans Player.

    Attributes
    ----------
    achievement_cls: :class:`Achievement`
        The constructor used to create the :attr:`Player.achievements` list.
        This must inherit from :class:`Achievement`.
    hero_cls: :class:`Hero`
        The constructor used to create the :attr:`Player.heroes` list. This must inherit from :class:`Hero`.
    label_cls: :class:`Label`
        The constructor used to create the :attr:`Player.labels` list. This must inherit from :class:`Label`.
    spell_cls: :class:`Spell`
        The constructor used to create the :attr:`Player.spells` list. This must inherit from :class:`Spell`.
    troop_cls: :class:`Troop`
        The constructor used to create the :attr:`Player.troops` list. This must inherit from :class:`Troop`.
    equipment_cls: :class:`Equipment`
        The constructor used to create the :attr:`Player.equipment` list. This must inherit from :class:`Equipment`.
    attack_wins: :class:`int`
        The number of attacks the player has won this season.
    defense_wins: :class:`int`
        The number of defenses the player has won this season.
    best_trophies: :class:`int`
        The player's best recorded trophies for the home base.
    war_stars: :class:`int`
        The player's total war stars.
    town_hall_weapon: Optional[:class:`int`]
        The player's town hall weapon level, or ``None`` if it doesn't exist.
    builder_hall: :class:`int`
        The player's builder hall level, or 0 if it hasn't been unlocked.
    best_builder_base_trophies: :class:`int`
        The player's best builder base trophy count.
    clan_capital_contributions: :class:`int`
        The player's total contribution to clan capitals
    legend_statistics: Optional[:class:`LegendStatistics`]
        The player's legend statistics, or ``None`` if they have never been in the legend league.
    war_opted_in: Optional[:class:`bool`]
        Whether the player has selected that they are opted "in" (True) for wars, or opted "out" (False).
        This will be ``None`` if the player is not in a clan.
    """

    __slots__ = (
        "clan",
        "attack_wins",
        "defense_wins",
        "best_trophies",
        "war_stars",
        "town_hall_weapon",
        "builder_hall",
        "best_builder_base_trophies",
        "clan_capital_contributions",
        "legend_statistics",
        "war_opted_in",
        "_achievements",
        "_heroes",
        "_pets",
        "_equipment",
        "_labels",
        "_spells",
        "_home_troops",
        "_builder_troops",
        "_super_troops",
        "achievement_cls",
        "hero_cls",
        "label_cls",
        "spell_cls",
        "troop_cls",
        "pet_cls",
        "equipment_cls",

        "_iter_achievements",
        "_iter_heroes",
        "_iter_labels",
        "_iter_spells",
        "_iter_troops",
        "_iter_pets",
        "_iter_equipment",

        "_cs_labels",
        "_cs_achievements",
        "_cs_troops",
        "_cs_home_troops",
        "_cs_builder_troops",
        "_cs_siege_machines",
        "_cs_pets",
        "_cs_super_troops",
        "_cs_heroes",
        "_cs_spells",
        "_cs_equipment",

        "_game_files_loaded",
        "_load_game_data",

    )

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        self._achievements = None  # type: Optional[dict]
        self._heroes = None  # type: Optional[dict]
        self._spells = None  # type: Optional[dict]
        self._home_troops: dict = {}
        self._builder_troops: dict = {}
        self._super_troops: list = []
        self._pets = None  # type: Optional[dict]
        self._equipment: Optional[dict] = None

        self.achievement_cls = Achievement
        self.hero_cls = Hero
        self.label_cls = Label
        self.spell_cls = Spell
        self.troop_cls = Troop
        self.pet_cls = Pet
        self.equipment_cls = Equipment

        if self._client and self._client._troop_holder.loaded:
            self._game_files_loaded = True
        else:
            self._game_files_loaded = False

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client and self._client.load_game_data.never:
            self._load_game_data = False
        else:
            self._load_game_data = True

        super().__init__(data=data, client=client)

    def _from_data(self, data: dict) -> None:
        super()._from_data(data)
        data_get = data.get

        self.attack_wins: int = data_get("attackWins")
        self.defense_wins: int = data_get("defenseWins")
        self.best_trophies: int = data_get("bestTrophies")
        self.war_stars: int = data_get("warStars")
        self.town_hall_weapon: int = data_get("townHallWeaponLevel")
        self.builder_hall: int = data_get("builderHallLevel", 0)
        self.best_builder_base_trophies: int = data_get("bestBuilderBaseTrophies")
        self.clan_capital_contributions: int = data_get("clanCapitalContributions")
        self.legend_statistics = try_enum(LegendStatistics, data=data_get("legendStatistics"))

        try:
            self.war_opted_in: Optional[bool] = True if data["warPreference"] == "in" else False
        except KeyError:
            # not in a clan / war preference not there
            self.war_opted_in: Optional[bool] = None

        label_cls = self.label_cls
        achievement_cls = self.achievement_cls
        troop_loader = self._client._troop_holder.load if self._client else None
        hero_loader = self._client._hero_holder.load if self._client else None
        spell_loader = self._client._spell_holder.load if self._client else None
        pet_loader = self._client._pet_holder.load if self._client else None
        equipment_loader = self._client._equipment_holder.load if self._client else None

        if self._game_files_loaded:
            pet_lookup = [p.name for p in self._client._pet_holder.items]
            equipment_lookup = [e.name for e in self._client._equipment_holder.items]
        else:
            pet_lookup = PETS_ORDER
            equipment_lookup = EQUIPMENT

        self._iter_labels = (label_cls(data=ldata, client=self._client) for ldata in data_get("labels", []))
        self._iter_achievements = (achievement_cls(data=adata) for adata in data_get("achievements", []))
        self._iter_troops = (
            troop_loader(
                data=tdata,
                townhall=self.town_hall,
                default=self.troop_cls,
                load_game_data=self._load_game_data,
            ) for tdata in data_get("troops", []) if tdata["name"] not in pet_lookup
        )

        self._iter_heroes = (
            hero_loader(
                data=hdata,
                townhall=self.town_hall,
                default=self.hero_cls,
                load_game_data=self._load_game_data,
            ) for hdata in data_get("heroes", [])
        )

        self._iter_spells = (
            spell_loader(
                data=sdata,
                townhall=self.town_hall,
                default=self.spell_cls,
                load_game_data=self._load_game_data,
            ) for sdata in data_get("spells", [])
        )

        self._iter_pets = (
            pet_loader(
                data=tdata,
                townhall=self.town_hall,
                default=self.pet_cls,
                load_game_data=self._load_game_data,
            ) for tdata in data_get("troops", []) if tdata["name"] in pet_lookup
        )

        self._iter_equipment = (
            equipment_loader(
                data=edata,
                townhall=self.town_hall,
                default=self.equipment_cls,
                load_game_data=self._load_game_data,
            ) for edata in data_get('heroEquipment', []) if edata['name'] in equipment_lookup
        )

    def _inject_clan_member(self, member):
        if member:
            self.clan_rank = getattr(member, "clan_rank", None)
            self.clan_previous_rank = getattr(member, "clan_previous_rank", None)

    def load_game_data(self):
        """Load game data for this player's troops and spells.

        .. note::

            This is not the preferred way to load game data.
            The best way to load game data is to pass ``load_game_data=True`` into your ``get_player`` call,
            or to have ``load_game_data=LoadGameData(default=True)`` in your client initiation.

            This method is provided as a utility for events where loading game data is not desirable unless a
            change has been observed.

        .. note::

            This operation may be slow if you have not loaded the game files during the current session yet.

        """
        # if self._game_files_loaded:
        #     return True

        holders = (self._client._troop_holder, self._client._hero_holder, self._client._spell_holder,
                   self._client._pet_holder, self._client._equipment_holder)
        if not all(holder.loaded for holder in holders):
            self._client._load_holders()

        for items, holder in zip((self.troops, self.heroes, self.spells, self.pets, self.equipment), holders):
            for item in items:
                if not item.is_loaded:
                    if isinstance(item, Troop):
                        base = holder.get(item.name, item.is_home_base)
                        item._load_from_parent(base)
                    else:
                        item._load_from_parent(holder.get(item.name))

    @cached_property("_cs_labels")
    def labels(self) -> List[Label]:
        """List[:class:`Label`]: A :class:`List` of :class:`Label`\s that the player has."""
        return list(self._iter_labels)

    @cached_property("_cs_achievements")
    def achievements(self) -> List[Achievement]:
        """List[:class:`Achievement`]: A list of the player's achievements."""
        # at the time of writing, the API presents achievements in the order
        # added to the game which doesn't match in-game order.
        achievement_dict = {a.name: a for a in self._iter_achievements}
        sorted_achievements = {}
        for name in ACHIEVEMENT_ORDER:
            try:
                sorted_achievements[name] = achievement_dict[name]
            except KeyError:
                continue

        self._achievements = sorted_achievements
        return list(sorted_achievements.values())

    def get_achievement(self, name: str, default_value=None) -> Optional[Achievement]:
        """Gets an achievement with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of an achievement as found in-game.
        default_value
            The value to return if the ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Achievement`]
            The returned achievement or the ``default_value`` if not found, which defaults to ``None``.
        """
        if not self._achievements:
            _ = self.achievements

        try:
            return self._achievements[name]
        except KeyError:
            return default_value

    @cached_property("_cs_troops")
    def troops(self) -> List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's :class:`Troop`.

        Troops are **not** ordered in this attribute. Use either :attr:`Player.home_troops`
        or :attr:`Player.builder_troops` if you want an ordered list.

        This includes:
        - Elixir Troops (Barbarian, Balloon, etc.)
        - Dark Elixir Troops (Minion, Hog Rider, etc.)
        - Siege Machines (Log Launcher, etc.)
        - **Boosted** Super Troops
        - Builder Troops (Raged Barbarian, etc.)

        This **does not** include:
        - Heroes
        - Hero Pets
        - Spells
        - Un-boosted Super Troops
        """
        loaded = self._game_files_loaded
        troops = []

        for troop in self._iter_troops:
            if (loaded and troop.is_super_troop) or troop.name in SUPER_TROOP_ORDER:
                self._super_troops.append(troop)
                if troop.is_active:
                    self._home_troops[troop.name] = troop
                    troops.append(troop)

            elif troop.is_home_base:
                self._home_troops[troop.name] = troop
                troops.append(troop)
            elif troop.is_builder_base:
                self._builder_troops[troop.name] = troop
                troops.append(troop)

        return troops

    @cached_property("_cs_home_troops")
    def home_troops(self) -> List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's home-base :class:`Troop`.

        This will return troops in the order found in both barracks and laboratory in-game.

        This includes:
        - Elixir Troops (Barbarian, Balloon, etc.)
        - Dark Elixir Troops (Minion, Hog Rider, etc.)
        - Siege Machines (Log Launcher, etc.)
        - **Boosted** Super Troops
        """
        order = {k: v for v, k in enumerate(HOME_TROOP_ORDER)}

        if not self._home_troops:
            _ = self.troops

        return list(sorted(self._home_troops.values(), key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_builder_troops")
    def builder_troops(self) -> List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's builder-base :class:`Troop`.

        This will return troops in the order found in both barracks and laboratory in-game.

        This includes:
        - Builder troops
        """
        order = {k: v for v, k in enumerate(BUILDER_TROOPS_ORDER)}

        if not self._builder_troops:
            _ = self.troops

        return list(sorted(self._builder_troops.values(), key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_siege_machines")
    def siege_machines(self) -> List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's siege-machine :class:`Troop`.

        This will return siege machines in the order found in both barracks and laboratory in-game.

        This includes:
        - Siege machines only.
        """
        order = {k: v for v, k in enumerate(SIEGE_MACHINE_ORDER)}
        troops = (t for t in self.troops if t.name in SIEGE_MACHINE_ORDER or t.is_siege_machine)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_pets")
    def pets(self) -> List[Pet]:
        """List[:class:`Pet`]: A :class:`List` of the player's hero pets.

        This will return hero pets in the order found in the Pet House in-game.

        This includes:
        - Hero pets only.
        """
        order = {k: v for v, k in enumerate(PETS_ORDER)}
        pets = list(sorted(self._iter_pets, key=lambda t: order.get(t.name, 0)))
        self._pets = {p.name: p for p in pets}
        return pets

    def get_pet(self, name: str, default_value=None) -> Optional[Pet]:
        """Gets the pet with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a pet as found in-game.
        default_value:
            The default value to return if a pet with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Pet`]
            The returned pet or the ``default_value`` if not found, which defaults to ``None``.

        """
        if not self._pets:
            _ = self.pets

        try:
            return self._pets[name]
        except KeyError:
            return default_value

    @cached_property('_cs_equipment')
    def equipment(self) -> List[Equipment]:
        """List[:class:`Equipment`]: A :class:`List` of the player's hero equipment.

        This will return hero equipment in the order it is in the player's profile

        This includes:
        - Hero equipment only.
        """
        order = {k: v for v, k in enumerate(EQUIPMENT)}
        equipment = list(sorted(self._iter_equipment, key=lambda t: order.get(t.name, 0)))
        self._equipment = {e.name: e for e in equipment}
        return equipment

    def get_equipment(self, name: str, default_value=None) -> Optional[Equipment]:
        """Gets the hero equipment with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a hero equipment as found in-game.
        default_value:
            The default value to return if a hero equipment with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Equipment`]
            The returned hero equipment or the ``default_value`` if not found, which defaults to ``None``.
        """
        if not self._equipment:
            _ = self.equipment

        try:
            return self._equipment[name]
        except KeyError:
            return default_value

    @cached_property("_cs_super_troops")
    def super_troops(self) -> List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's super troops.

        This will return super troops in the order found in the super troop boosting building, in game.

        This includes:
        - All super troops, boosted or not.
        """
        order = {k: v for v, k in enumerate(SUPER_TROOP_ORDER)}

        if not self._super_troops:
            _ = self.troops

        return list(sorted(self._super_troops, key=lambda t: order.get(t.name, 0)))

    def get_troop(self, name: str, is_home_troop=None, default_value=None) -> Optional[Troop]:
        """Gets a troop with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a troop as found in-game.
        is_home_troop: :class:`bool`
            Whether the troop you're trying to find is a home troop. This changes how the lookup is done,
            in order to facilitate searching for a ``Baby Dragon``. By default, this will search from both
            builder and home troops.
        default_value
            The value to return if the ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Troop`]
            The returned troop or the ``default_value`` if not found, which defaults to ``None``.
        """
        _ = self.troops

        if is_home_troop is None:
            lookup = {**self._builder_troops, **self._home_troops}
        elif is_home_troop is True:
            lookup = self._home_troops
        elif is_home_troop is False:
            lookup = self._builder_troops
        else:
            raise TypeError("is_home_troop must be of type bool not {0!r}".format(is_home_troop))

        try:
            return lookup[name]
        except KeyError:
            return default_value

    @cached_property("_cs_heroes")
    def heroes(self) -> List[Hero]:
        """List[:class:`Hero`]: A :class:`List` of the player's :class:`Hero`.

        This will return heroes in the order found in the store and laboratory in-game.
        """
        heroes_dict = {h.name: h for h in self._iter_heroes}
        sorted_heroes = {}
        for name in HERO_ORDER:
            # have to do it this way because it's less expensive than removing None's if they don't have a troop.
            try:
                sorted_heroes[name] = heroes_dict[name]
            except KeyError:
                continue

        self._heroes = sorted_heroes
        return list(sorted_heroes.values())

    def get_hero(self, name: str, default_value=None) -> Optional[Hero]:
        """Gets the hero with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a hero as found in-game.
        default_value:
            The default value to return if a hero with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Hero`]
            The returned hero or the ``default_value`` if not found, which defaults to ``None``.

        """
        if not self._heroes:
            _ = self.heroes

        try:
            return self._heroes[name]
        except KeyError:
            return default_value

    @cached_property("_cs_spells")
    def spells(self) -> List[Spell]:
        """List[:class:`Spell`]: A :class:`List` of the player's :class:`Spell` ordered as they appear in-game.

        This will return spells in the order found in both spell factory and laboratory in-game.
        """
        self._spells = {s.name: s for s in self._iter_spells}
        dict_spells = self._spells
        order = {k: v for v, k in enumerate(SPELL_ORDER)}

        return list(sorted(
                dict_spells.values(),
                key=lambda s: order.get(s.name, 0)))

    def get_spell(self, name: str, default_value=None) -> Optional[Spell]:
        """Gets the spell with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a spell as found in-game.
        default_value:
            The default value to return if a spell with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Spell`]
            The returned spell or the ``default_value`` if not found, which defaults to ``None``.
        """
        if not self._spells:
            _ = self.spells

        try:
            return self._spells[name]
        except KeyError:
            return default_value

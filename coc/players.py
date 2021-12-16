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
import typing


from .miscmodels import try_enum, Achievement, Label, League, LegendStatistics
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
    HERO_PETS_ORDER,
)
from .abc import BasePlayer
from .hero import Hero, Pet
from .player_clan import PlayerClan
from .spell import Spell
from .troop import Troop
from .utils import cached_property


if typing.TYPE_CHECKING:
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
    trophies: :class:`int`
        The member's trophy count.
    versus_trophies: :class:`int`
        The member's versus trophy count.
    clan_rank: :class:`int`
        The member's rank in the clan.
    clan_previous_rank: :class:`int`
        The member's rank before the last leaderboard change
        (ie if Bob overtakes Jim in trophies, and they switch ranks on the leaderboard,
        and you want to find out their previous rankings, this will help.).
    donations: :class:`int`
        The member's donation count for this season.
    received: :class:`int`
        The member's donations received count for this season.
    clan_cls: :class:`coc.Clan`
        The class to use to create the :attr:`ClanMember.clan` attribute.
        Ensure any overriding of this inherits from :class:`coc.Clan` or :class:`coc.PlayerClan`.
    league_cls: :class:`coc.League`
        The class to use to create the :attr:`Clanmember.league` attribute.
        Ensure any overriding of this inherits from :class:`coc.League`.
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

    def __init__(self, *, data, client, clan=None, **_):
        super().__init__(data=data, client=client)
        self._client = client
        self.clan_cls = PlayerClan
        self.league_cls = League
        self._from_data(data)
        if clan:
            self.clan = clan

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.exp_level: int = data_get("expLevel")
        self.trophies: int = data_get("trophies")
        self.versus_trophies: int = data_get("versusTrophies")
        self.clan_rank: int = data_get("clanRank")
        self.clan_previous_rank: int = data_get("previousClanRank")
        self.donations: int = data_get("donations")
        self.received: int = data_get("donationsReceived")

        self.clan = try_enum(self.clan_cls, data=data_get("clan"), client=self._client)
        self.league = try_enum(self.league_cls, data=data_get("league") or UNRANKED_LEAGUE_DATA, client=self._client)
        self.role = data_get("role") and Role(value=data["role"])

    async def get_detailed_clan(self) -> typing.Optional["Clan"]:
        """Get detailed clan details for the player's clan. If the player's clan is ``None``,this will return ``None``.

        Example
        ---------

        .. code-block:: python3

            player = await client.get_player('tag')
            clan = await player.get_detailed_clan()
        """
        return self.clan and await self._client.get_clan(self.clan.tag)


class RankedPlayer(ClanMember):
    """Represents a leaderboard-ranked player.

    Attributes
    ----------
    attack_wins: :class:`int`
        The player's number of attack wins. If retrieving info for versus leader-boards, this will be ``None``.
    defense_wins: :class:`int`
        The player's number of defense wins. If retrieving info for versus leader-boards, this will be ``None``.
    versus_trophies: :class:`int`
        The player's versus trophy count. If retrieving info for regular leader-boards, this will be ``None``.
    rank: :class:`int`
        The player's rank in the clan leaderboard.
    previous_rank: :class:`int`
        The member's rank before the last clan leaderboard change
        (ie if Bob overtakes Jim in trophies, and they switch ranks on the leaderboard,
        and you want to find out their previous rankings, this will help.).
    """

    __slots__ = ("attack_wins", "defense_wins", "versus_trophies", "rank", "previous_rank")

    def _from_data(self, data: dict) -> None:
        super()._from_data(data)

        data_get = data.get
        self.attack_wins: int = data_get("attackWins")
        self.defense_wins: int = data_get("defenseWins")
        self.versus_trophies: int = data_get("versusTrophies")
        self.rank: int = data_get("rank")
        self.previous_rank: int = data_get("previousRank")


class Player(ClanMember):
    """Represents a Clash of Clans Player.

    Attributes
    ----------
    achievement_cls: :class:`Achievement`
        The constructor used to create the :attr:`Player.achievements` list. This must inherit :class:`Achievement`.
    hero_cls: :class:`Hero`
        The constructor used to create the :attr:`Player.heroes` list. This must inherit from :class:`Hero`.
    label_cls: :class:`Label`
        The constructor used to create the :attr:`Player.labels` list. This must inherit from :class:`Label`.
    spell_cls: :class:`Spell`
        The constructor used to create the :attr:`Player.spells` list. This must inherit from :class:`Spell`.
    troop_cls: :class:`Troop`
        The constructor used to create the :attr:`Player.troops` list. This must inherit from :class:`Troop`.
    attack_wins: :class:`int`
        The number of attacks the player has won this season.
    defense_wins: :class:`int`
        The number of defenses the player has won this season.
    best_trophies: :class:`int`
        The player's best recorded trophies for the home base.
    war_stars: :class:`int`
        The player's total war stars.
    town_hall: :class:`int`
        The player's town hall level.
    town_hall_weapon: Optional[:class:`int`]
        The player's town hall weapon level, or ``None`` if it doesn't exist.
    builder_hall: :class:`int`
        The player's builder hall level, or 0 if it hasn't been unlocked.
    best_versus_trophies: :class:`int`
        The player's best versus trophy count.
    versus_attack_wins: :class:`int`
        The number of versus attacks the player has won
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
        "town_hall",
        "town_hall_weapon",
        "builder_hall",
        "best_versus_trophies",
        "versus_attack_wins",
        "legend_statistics",
        "war_opted_in",
        "_achievements",
        "_heroes",
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

        "_iter_achievements",
        "_iter_heroes",
        "_iter_labels",
        "_iter_spells",
        "_iter_troops",
        "_iter_pets",

        "_cs_labels",
        "_cs_achievements",
        "_cs_troops",
        "_cs_home_troops",
        "_cs_builder_troops",
        "_cs_siege_machines",
        "_cs_hero_pets",
        "_cs_super_troops",
        "_cs_heroes",
        "_cs_spells",

        "_game_files_loaded",
        "_load_game_data",

    )

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        self._achievements = None  # type: typing.Optional[dict]
        self._heroes = None  # type: typing.Optional[dict]
        self._spells = None  # type: typing.Optional[dict]
        self._home_troops: dict = {}
        self._builder_troops: dict = {}
        self._super_troops: list = []

        self.achievement_cls = Achievement
        self.hero_cls = Hero
        self.label_cls = Label
        self.spell_cls = Spell
        self.troop_cls = Troop
        self.pet_cls = Pet

        if self._client._troop_holder.loaded:
            self._game_files_loaded = True
        else:
            self._game_files_loaded = False

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client.load_game_data.never:
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
        self.town_hall: int = data_get("townHallLevel")
        self.town_hall_weapon: int = data_get("townHallWeaponLevel")
        self.builder_hall: int = data_get("builderHallLevel", 0)
        self.best_versus_trophies: int = data_get("bestVersusTrophies")
        self.versus_attack_wins: int = data_get("versusBattleWins")
        self.legend_statistics = try_enum(LegendStatistics, data=data_get("legendStatistics"))

        try:
            self.war_opted_in: typing.Optional[bool] = True if data["warPreference"] == "in" else False
        except KeyError:
            # not in a clan / war preference not there
            self.war_opted_in: typing.Optional[bool] = None

        label_cls = self.label_cls
        achievement_cls = self.achievement_cls
        troop_loader = self._client._troop_holder.load
        hero_loader =  self._client._hero_holder.load
        spell_loader = self._client._spell_holder.load
        pet_loader = self._client._pet_holder.load

        if self._game_files_loaded:
            pet_lookup = [p.name for p in self._client._pet_holder.items]
        else:
            pet_lookup = HERO_PETS_ORDER

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

        holders = (self._client._troop_holder, self._client._hero_holder, self._client._spell_holder)
        if not all(holder.loaded for holder in holders):
            self._client._load_holders()

        for items, holder in zip((self.troops, self.heroes, self.spells), holders):
            for item in items:
                if not item.is_loaded:
                    if isinstance(item, Troop):
                        base = holder.get(item.name, item.is_home_base)
                        item._load_from_parent(base)
                    else:
                        item._load_from_parent(holder.get(item.name))

    @cached_property("_cs_labels")
    def labels(self) -> typing.List[Label]:
        """List[:class:`Label`]: A :class:`List` of :class:`Label` that the player has."""
        return list(self._iter_labels)

    @cached_property("_cs_achievements")
    def achievements(self) -> typing.List[Achievement]:
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

    def get_achievement(self, name: str, default_value=None) -> typing.Optional[Achievement]:
        """Returns an achievement with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of an achievement as found in-game.
        default_value
            The value to return if the ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Achievement`]
            The returned achievement or the ``default_value`` if not found, which defaults to ``None``..
        """
        if not self._achievements:
            _ = self.achievements

        try:
            return self._achievements[name]
        except KeyError:
            return default_value

    @cached_property("_cs_troops")
    def troops(self) -> typing.List[Troop]:
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
    def home_troops(self) -> typing.List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's home-base :class:`Troop`.

        This will return troops in the order found in both barracks and labatory in-game.

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
    def builder_troops(self) -> typing.List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's builder-base :class:`Troop`.

        This will return troops in the order found in both barracks and labatory in-game.

        This includes:
        - Builder troops
        """
        order = {k: v for v, k in enumerate(BUILDER_TROOPS_ORDER)}

        if not self._builder_troops:
            _ = self.troops

        return list(sorted(self._builder_troops.values(), key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_siege_machines")
    def siege_machines(self) -> typing.List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's siege-machine :class:`Troop`.

        This will return siege machines in the order found in both barracks and labatory in-game.

        This includes:
        - Siege machines only.
        """
        order = {k: v for v, k in enumerate(SIEGE_MACHINE_ORDER)}
        troops = (t for t in self.troops if t.name in SIEGE_MACHINE_ORDER or t.is_siege_machine)
        return list(sorted(troops, key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_hero_pets")
    def hero_pets(self) -> typing.List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's hero pets.

        This will return hero pets in the order found in the Pet House in-game.

        This includes:
        - Hero pets only.
        """
        order = {k: v for v, k in enumerate(HERO_PETS_ORDER)}
        return list(sorted(self._iter_pets, key=lambda t: order.get(t.name, 0)))

    @cached_property("_cs_super_troops")
    def super_troops(self) -> typing.List[Troop]:
        """List[:class:`Troop`]: A :class:`List` of the player's super troops.

        This will return super troops in the order found in the super troop boosting building, in game.

        This includes:
        - All super troops, boosted or not.
        """
        order = {k: v for v, k in enumerate(SUPER_TROOP_ORDER)}

        if not self._super_troops:
            _ = self.troops

        return list(sorted(self._super_troops, key=lambda t: order.get(t.name, 0)))

    def get_troop(self, name: str, is_home_troop=None, default_value=None) -> typing.Optional[Troop]:
        """Returns a troop with the given name.

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
            The returned troop or the ``default_value`` if not found, which defaults to ``None``..
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
    def heroes(self) -> typing.List[Hero]:
        """List[:class:`Hero`]: A :class:`List` of the player's :class:`Hero`.

        This will return heroes in the order found in the store and labatory in-game.
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

    def get_hero(self, name: str, default_value=None) -> typing.Optional[Hero]:
        """Returns a hero with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a hero as found in-game.
        default_value:
            The default value to return if a hero with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Hero`]
            The returned hero or the ``default_value`` if not found, which defaults to ``None``..
        """
        if not self._heroes:
            _ = self.heroes

        try:
            return self._heroes[name]
        except KeyError:
            return default_value

    @cached_property("_cs_spells")
    def spells(self) -> typing.List[Spell]:
        """List[:class:`Spell`]: A :class:`List` of the player's :class:`Spell` ordered as they appear in-game.

        This will return spells in the order found in both spell factory and labatory in-game.
        """
        dict_spells = self._spells = {s.name: s for s in self._iter_spells}
        order = {k: v for v, k in enumerate(SPELL_ORDER)}
        return list(sorted(dict_spells.values(), key=lambda s: order.get(s.name)))

    def get_spell(self, name: str, default_value=None) -> typing.Optional[Spell]:
        """Returns a spell with the given name.

        Parameters
        -----------
        name: :class:`str`
            The name of a spell as found in-game.
        default_value:
            The default value to return if a spell with ``name`` is not found. Defaults to ``None``.

        Returns
        --------
        Optional[:class:`Spell`]
            The returned spell or the ``default_value`` if not found, which defaults to ``None``..
        """
        if not self._spells:
            _ = self.spells

        try:
            return self._spells[name]
        except KeyError:
            return default_value

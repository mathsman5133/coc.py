from typing import Dict, List, Optional, Tuple, Type
from pathlib import Path

import ujson

from .abc import DataContainer, DataContainerHolder
from .enums import Resource
from .miscmodels import TimeDelta, try_enum
from .utils import UnitStat


TROOPS_FILE_PATH = Path(__file__).parent.joinpath(Path("static/characters.json"))
SUPER_TROOPS_FILE_PATH = Path(__file__).parent.joinpath(Path("static/supers.json"))


class Troop(DataContainer):
    """Represents a Troop object as returned by the API, optionally filled with game data.

    +----------------------------------+-------------------+
    |               Name               |       Type        |
    +----------------------------------+-------------------+
    |         :attr:`Troop.id`         |   :class:`int`    |
    +----------------------------------+-------------------+
    |        :attr:`Troop.name`        |        str        |
    +----------------------------------+-------------------+
    |       :attr:`Troop.range`        |        int        |
    +----------------------------------+-------------------+
    |        :attr:`Troop.dps`         |        int        |
    +----------------------------------+-------------------+
    |     :attr:`Troop.hitpoints`      |        int        |
    +----------------------------------+-------------------+
    |   :attr:`Troop.ground_target`    |       bool        |
    +----------------------------------+-------------------+
    |       :attr:`Troop.speed`        |        int        |
    +----------------------------------+-------------------+
    |    :attr:`Troop.upgrade_cost`    |        int        |
    +----------------------------------+-------------------+
    |  :attr:`Troop.upgrade_resource`  | :class:`Resource` |
    +----------------------------------+-------------------+
    |    :attr:`Troop.upgrade_time`    |   :class:`TimeDelta`   |
    +----------------------------------+-------------------+
    |   :attr:`Troop.training_cost`    |        int        |
    +----------------------------------+-------------------+
    | :attr:`Troop.training_resource`  | :class:`Resource` |
    +----------------------------------+-------------------+
    |   :attr:`Troop.training_time`    |   :class:`TimeDelta`   |
    +----------------------------------+-------------------+
    |  :attr:`Troop.is_elixir_troop`   |   :class:`bool`   |
    +----------------------------------+-------------------+
    |   :attr:`Troop.is_dark_troop`    |   :class:`bool`   |
    +----------------------------------+-------------------+
    |  :attr:`Troop.is_siege_machine`  |   :class:`bool`   |
    +----------------------------------+-------------------+
    |   :attr:`Troop.is_super_troop`   |   :class:`bool`   |
    +----------------------------------+-------------------+
    |      :attr:`Troop.cooldown`      |   :class:`TimeDelta`   |
    +----------------------------------+-------------------+
    |      :attr:`Troop.duration`      |   :class:`TimeDelta`   |
    +----------------------------------+-------------------+
    | :attr:`Troop.min_original_level` |        int        |
    +----------------------------------+-------------------+
    |   :attr:`Troop.original_troop`   |  :class:`Troop`   |
    +----------------------------------+-------------------+
    |     :attr:`Troop.is_loaded`      |       bool        |
    +----------------------------------+-------------------+
    |       :attr:`Troop.level`        |        int        |
    +----------------------------------+-------------------+
    |     :attr:`Troop.max_level`      |        int        |
    +----------------------------------+-------------------+
    |      :attr:`Troop.village`       |        str        |
    +----------------------------------+-------------------+

    Attributes
    ----------
    id: :class:`int`
        The troop's unique ID.
    name: str
        The troop's name.
    range: int
        The troop's attack range.
    lab_level: int
        The required labatory level to upgrade the troop to this level.
    dps: int
        The troop's Damage Per Second (DPS).
    hitpoints: int
        The number of hitpoints the troop has at this level.
    ground_target: bool
        Whether the troop is ground-targetting.
    speed: int
        The troop's speed.
    upgrade_cost: int
        The amount of resources required to upgrade the troop to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this troop.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this troop to the next level.
    training_cost: int
        The amount of resources required to train this troop.
    training_resource: :class:`Resource`
        The type of resource used to train this troop.
    training_time: :class:`TimeDelta`
        The amount of time required to train this troop.
    is_elixir_troop: :class:`bool`
        Whether this troop is a regular troop from the Barracks
    is_dark_troop: :class:`bool`
        Whether this troop is a dark-troop, trained in the Dark Barracks.
    is_siege_machine: :class:`bool`
        Whether this troop is a Siege Machine.
    is_super_troop: :class:`bool`
        Whether this troop is a Super Troop.

    cooldown: :class:`TimeDelta`
        The cooldown on this super troop before being able to be reactivated [Super Troops Only].
    duration: :class:`TimeDelta`
        The length of time this super troop is active for [Super Troops Only].
    min_original_level: int
        The minimum level required of the original troop in order to boost this troop [Super Troops Only].
    original_troop: :class:`Troop`
        The "original" counterpart troop to this super troop [Super Troops Only].

    is_loaded: bool
        Whether the API data has been loaded for this troop.
    level: int
        The troop's level
    max_level: int
        The max level for this troop.
    village: str
        Either ``home`` or ``builderBase``, indicating which village this troop belongs to.
    """
    name: str
    level: int
    max_level: int
    village: str
    is_active: bool

    id: int
    range: int
    dps: int
    ground_target: bool
    speed: int
    upgrade_cost: int
    upgrade_resource: "Resource"
    upgrade_time: "TimeDelta"
    training_cost: int
    training_resource: "Resource"
    training_time: "TimeDelta"

    cooldown: "TimeDelta"
    duration: "TimeDelta"
    min_original_level: int
    original_troop: "Troop"

    is_elixir_troop: bool = False
    is_dark_troop: bool = False
    is_siege_machine: bool = False
    is_super_troop: bool = False
    is_loaded: bool = False

    @classmethod
    def _inject_super_meta(cls, troop_meta):
        cls.is_super_troop = True

        cls.cooldown = try_enum(UnitStat, [TimeDelta(hours=hours) for hours in troop_meta.get("CooldownH", [])])
        cls.duration = try_enum(UnitStat, [TimeDelta(hours=hours) for hours in troop_meta.get("DurationH", [])])
        cls.min_original_level = troop_meta["MinOriginalLevel"][0]
        cls._original = troop_meta["Original"][0]

        return cls

    @property
    def is_max_for_townhall(self):
        """:class:`bool`:
            Returns a boolean that indicates whether the troop is the max level for the player's townhall level.
        """
        if self.is_max:
            return True

        # 1. Hero/troop levels in-game are 1-indexed, UnitStat is 1-indexed
        # 2. TH-lab levels in-game and here are 1-indexed
        # 3. We then want to check that for the level less than this troop the req'd
        #    TH is less than or equal to current TH,
        #    and for troop level above, it requires a higher TH than we currently have.
        #    Maybe there's a better way to go about doing this.
        return self.lab_to_townhall[self.__class__.lab_level[self.level]] <= self._townhall \
                    < self.lab_to_townhall[self.__class__.lab_level[self.level + 1]]

    @classmethod
    def get_max_level_for_townhall(cls, townhall):
        """Get the maximum level for a troop for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum troop level for.

        Returns
        --------
        :class:`int`
            The maximum troop level, or ``None`` if the troop hasn't been unlocked at that level.

        """
        for lab_level, th_level in cls.lab_to_townhall.items():
            if th_level != townhall:
                continue

            levels = [troop_level for troop_level, lab in enumerate(cls.lab_level, start=1) if lab <= lab_level]
            return levels and max(levels) or None

        raise ValueError("The townhall level was not valid.")


class TroopHolder(DataContainerHolder):
    items: List[Type[Troop]] = []
    item_lookup: Dict[Tuple[str, bool], Type[Troop]]

    def _load_json(self, object_ids, english_aliases, lab_to_townhall):
        with open(TROOPS_FILE_PATH) as fp:
            troop_data = ujson.load(fp)
        with open(SUPER_TROOPS_FILE_PATH) as fp:
            super_troop_data = ujson.load(fp)

        super_data = {meta["Replacement"][0]: meta for _, meta in super_troop_data.items()}

        for supercell_name, troop_meta in troop_data.items():
            if not troop_meta.get("TID"):
                continue
            if "Tutorial" in supercell_name:
                continue
            if "DisableProduction" in troop_meta:
                continue

            new_troop: Type[Troop] = type('Troop', Troop.__bases__, dict(Troop.__dict__))
            new_troop._load_json_meta(
                troop_meta,
                id=object_ids[supercell_name],
                name=english_aliases[troop_meta["TID"][0]][0],
                lab_to_townhall=lab_to_townhall,
            )
            self.items.append(new_troop)
            self.item_lookup[(new_troop.name, new_troop._is_home_village)] = new_troop

            try:
                super_meta = super_data[supercell_name]
            except KeyError:
                pass
            else:
                new_troop._inject_super_meta(super_meta)

        for troop in filter(lambda t: t.is_super_troop, self.items):
            sc_name = troop_data[troop._original]["TID"][0]
            troop.original_troop = self.get(english_aliases[sc_name][0])

        self.loaded = True

    def load(self, data, townhall: int, default: "Troop" = Troop, load_game_data: bool = None) -> Troop:
        if load_game_data is True:
            try:
                troop = self.item_lookup[(data["name"], data["village"] == "home")]
            except KeyError:
                troop = default
        else:
            troop = default

        return troop(data=data, townhall=townhall)

    def get(self, name, home_village=True) -> Optional[Type[Troop]]:
        try:
            return self.item_lookup[(name, home_village)]
        except KeyError:
            return None


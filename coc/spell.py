from typing import Type, Dict, List
from pathlib import Path

from .abc import DataContainer, DataContainerHolder
from .enums import Resource
from .miscmodels import TimeDelta


SPELLS_FILE_PATH = Path(__file__).parent.joinpath(Path("static/spells.json"))


class Spell(DataContainer):
    """Represents a Spell object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: int
        The spell's unique ID.
    name: str
        The spell's name.
    range: int
        The spell's attack range.
    upgrade_cost: int
        The amount of resources required to upgrade the spell to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this spell.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this spell to the next level.
    training_cost: int
        The amount of resources required to train this spell.
    training_resource: :class:`Resource`
        The type of resource used to train this spell.
    training_time: :class:`TimeDelta`
        The amount of time required to train this spell.
    is_elixir_spell: :class:`bool`
        Whether this spell is a regular spell from the Barracks
    is_dark_spell: :class:`bool`
        Whether this spell is a dark-spell, trained in the Dark Barracks.
    is_siege_machine: :class:`bool`
        Whether this spell is a Siege Machine.
    is_loaded: bool
        Whether the API data has been loaded for this spell.
    level: int
        The spell's level
    max_level: int
        The max level for this spell.
    village: str
        Either ``home`` or ``builderBase``, indicating which village this spell belongs to.
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

    is_elixir_spell: bool = False
    is_dark_spell: bool = False
    is_loaded: bool = False

    @property
    def is_max_for_townhall(self):
        """:class:`bool`:
            Returns a boolean that indicates whether the spell is the max level for the player's townhall level.
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
        """Get the maximum level for a spell for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum troop level for.

        Returns
        --------
        :class:`int`
            The maximum spell level, or ``None`` if the spell hasn't been unlocked at that level.

        """
        for lab_level, th_level in cls.lab_to_townhall.items():
            if th_level != townhall:
                continue

            levels = [spell_level for spell_level, lab in enumerate(cls.lab_level, start=1) if lab <= lab_level]
            return levels and max(levels) or None

        raise ValueError("The townhall level was not valid.")


class SpellHolder(DataContainerHolder):
    items: List[Type[Spell]] = []
    item_lookup: Dict[str, Type[Spell]]

    FILE_PATH = SPELLS_FILE_PATH
    data_object = Spell

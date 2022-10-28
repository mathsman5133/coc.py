from typing import TYPE_CHECKING, Dict, List, Type
from pathlib import Path

from .abc import DataContainer, DataContainerHolder

if TYPE_CHECKING:
    from .enums import Resource
    from .miscmodels import TimeDelta


HERO_FILE_PATH = Path(__file__).parent.joinpath(Path("static/heroes.json"))
PET_FILE_PATH = Path(__file__).parent.joinpath(Path("static/pets.json"))


class Hero(DataContainer):
    """Represents a Hero object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: int
        The hero's unique ID.
    name: str
        The hero's name.
    range: int
        The hero's attack range.
    dps: int
        The hero's Damage Per Second (DPS).
    hitpoints: int
        The number of hitpoints the troop has at this level.
    ground_target: bool
        Whether the hero is ground-targetting. The Grand Warden is classified as ground targetting always.
    speed: int
        The hero's speed.
    upgrade_cost: int
        The amount of resources required to upgrade the hero to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this hero.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this hero to the next level.
    ability_time: int
        The number of milliseconds the hero's ability lasts for.
    required_th_level: int
        The minimum required townhall to unlock this level of the hero.
    regeneration_time: :class:`TimeDelta`
        The time required for this hero to regenerate after being "knocked out".
    is_loaded: bool
        Whether the API data has been loaded for this hero.
    level: int
        The hero's level
    max_level: int
        The max level for this hero.
    village: str
        Either ``home`` or ``builderBase``, indicating which village this hero belongs to.
    """
    name: str
    level: int
    max_level: int
    village: str
    is_active: bool

    id: int
    range: int
    dps: int
    hitpoints: int
    ground_target: bool
    speed: int
    upgrade_cost: int
    upgrade_resource: "Resource"
    upgrade_time: "TimeDelta"
    ability_time: int
    required_th_level: int
    regeneration_time: "TimeDelta"
    is_loaded: bool = False

    @property
    def is_max_for_townhall(self) -> bool:
        """:class:`bool`: Returns whether the hero is the max level for the player's townhall level."""
        if self.is_max:
            return True

        return self._townhall < self.__class__.required_th_level[self.level]

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
            The maximum spell level.

        """
        return max(i for i, th in enumerate(cls.required_th_level, start=1) if th <= townhall)


class HeroHolder(DataContainerHolder):
    items: List[Type[Hero]] = []
    item_lookup: Dict[str, Type[Hero]]

    FILE_PATH = HERO_FILE_PATH
    data_object = Hero


class Pet(DataContainer):
    """Represents a Pet object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: int
        The pet's unique ID.
    name: str
        The pet's name.
    range: int
        The pet's attack range.
    dps: int
        The pet's Damage Per Second (DPS).
    ground_target: bool
        Whether the pet is ground-targetting.
    hitpoints: int
        The number of hitpoints the troop has at this level.
    speed: int
        The pet's speed.
    upgrade_cost: int
        The amount of resources required to upgrade the pet to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this pet.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this pet to the next level.
    is_loaded: bool
        Whether the API data has been loaded for this pet.
    level: int
        The pet's level
    max_level: int
        The max level for this pet.
    village: str
        Either ``home`` or ``builderBase``, indicating which village this pet belongs to.
    """
    name: str
    level: int
    max_level: int
    village: str
    is_active: bool

    id: int
    range: int
    dps: int
    hitpoints: int
    ground_target: bool
    speed: int
    upgrade_cost: int
    upgrade_resource: "Resource"
    upgrade_time: "TimeDelta"
    is_loaded: bool = False


class PetHolder(DataContainerHolder):
    items: List[Type[Pet]] = []
    item_lookup: Dict[str, Type[Pet]]

    FILE_PATH = PET_FILE_PATH
    data_object = Pet

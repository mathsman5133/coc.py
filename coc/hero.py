from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Type
from pathlib import Path

from .abc import DataContainer, DataContainerHolder

if TYPE_CHECKING:
    from .enums import Resource
    from .miscmodels import TimeDelta


HERO_FILE_PATH = Path(__file__).parent.joinpath(Path("static/heroes.json"))
PET_FILE_PATH = Path(__file__).parent.joinpath(Path("static/pets.json"))


class Hero(DataContainer):
    """
    Represents a Hero object as returned by the API, optionally
    filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The hero's unique ID.
    name: :class:`str`
        The hero's name.
    range: :class:`int`
        The hero's attack range.
    dps: :class:`int`
        The hero's Damage Per Second (DPS).
    hitpoints: :class:`int`
        The number of hitpoints the troop has at this level.
    ground_target: :class:`bool`
        Whether the hero is ground-targetting. The Grand Warden is classified as ground targetting always.
    speed: :class:`int`
        The hero's speed.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the hero to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this hero.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this hero to the next level.
    ability_time: :class:`int`
        The number of milliseconds the hero's ability lasts for.
    required_th_level: :class:`int`
        The minimum required townhall to unlock this level of the hero.
    regeneration_time: :class:`TimeDelta`
        The time required for this hero to regenerate after being "knocked out".
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this hero.
    level: :class:`int`
        The hero's level
    max_level: :class:`int`
        The max level for this hero.
    village: :class:`str`
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

    def __repr__(cls):
        attrs = [
            ("name", cls.name),
            ("id", cls.id),
        ]
        return "<%s %s>" % (
            cls.__name__, " ".join("%s=%r" % t for t in attrs),)

    @property
    def is_max_for_townhall(self) -> bool:
        """:class:`bool`: Returns whether the hero is the max level for the player's townhall level."""
        if self.is_max:
            return True

        return self._townhall < self.__class__.required_th_level[self.level]

    @classmethod
    def get_max_level_for_townhall(cls, townhall):
        """Get the maximum level for a hero for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum hero level for.

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
    id: :class:`int`
        The pet's unique ID.
    name: :class:`str`
        The pet's name.
    range: :class:`int`
        The pet's attack range.
    dps: :class:`int`
        The pet's Damage Per Second (DPS).
    ground_target: :class:`bool`
        Whether the pet is ground-targetting.
    hitpoints: :class:`int`
        The number of hitpoints the troop has at this level.
    speed: :class:`int`
        The pet's speed.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the pet to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this pet.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this pet to the next level.
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this pet.
    level: :class:`int`
        The pet's level
    max_level: :class:`int`
        The max level for this pet.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this pet belongs to.
    required_th_level: :class:`int`
        The minimum required townhall to unlock this level of the pet.
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
    required_th_level: int

    def __repr__(cls):
        attrs = [
            ("name", cls.name),
            ("id", cls.id),
        ]
        return "<%s %s>" % (
            cls.__name__, " ".join("%s=%r" % t for t in attrs),)

    @property
    def is_max_for_townhall(self) -> bool:
        """:class:`bool`: Returns whether the hero pet is the max level for the player's townhall level."""
        if self.is_max:
            return True

        return self._townhall < self.__class__.required_th_level[self.level]

    @classmethod
    def get_max_level_for_townhall(cls, townhall):
        """Get the maximum level for a hero pet for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum hero pet level for.

        Returns
        --------
        :class:`int`
            The maximum spell level.

        """
        return max(i for i, th in enumerate(cls.required_th_level, start=1) if th <= townhall)


class PetHolder(DataContainerHolder):
    items: List[Type[Pet]] = []
    item_lookup: Dict[str, Type[Pet]]

    FILE_PATH = PET_FILE_PATH
    data_object = Pet

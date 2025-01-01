import ujson

from typing import TYPE_CHECKING, Dict, List, Optional, Type
from pathlib import Path

from .abc import DataContainer, DataContainerHolder
from .miscmodels import try_enum
from .utils import UnitStat

from .enums import Resource

if TYPE_CHECKING:
    from .miscmodels import TimeDelta

HERO_FILE_PATH = Path(__file__).parent.joinpath(Path("static/heroes.json"))
PET_FILE_PATH = Path(__file__).parent.joinpath(Path("static/pets.json"))
EQUIPMENT_FILE_PATH = Path(__file__).parent.joinpath(Path("static/equipment.json"))


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
    equipment: :class:`List[Equipment]`
        a list of the equipment currently used by this hero
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
    equipment: List["Equipment"]

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

    def __init__(self, data, townhall):
        # super().__init__ call fails, hence copy & pasted the parent init
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]
        self.is_active: bool = data.get("superTroopIsActive")

        self._townhall = townhall

        # copies for a static hash
        self.__name = data['name']
        self.__level = data['level']
        self.__village = data['village']
        self.__is_active = data.get("superTroopIsActive")

        # end of copy & pasted init

        equipment = [try_enum(Equipment, equipment, townhall=townhall) for equipment in data.get('equipment', [])]
        self.equipment = [eq for eq in equipment if eq is not None]

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

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

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

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


class Equipment(DataContainer):
    """Represents a hero equipment object as returned by the API

        Attributes
        ----------
        name: :class:`str`
            The equipment's name.
        level: :class:`int`
            The equipment's level
        max_level: :class:`int`
            The max level for this equipment.
        village: :class:`str`
            Either ``home`` or ``builderBase``, indicating which village this equipment belongs to.
    """
    name: str
    level: int
    max_level: int
    village: str

    @classmethod
    def _load_json_meta(cls, json_meta, id, name, smithy_to_townhall):
        cls.id = int(id)
        cls.name = name
        cls.smithy_to_townhall = smithy_to_townhall

        cls._json_meta = json_meta
        smithy_levels = json_meta.get("RequiredBlacksmithLevel")
        levels_available = [key for key in json_meta.keys() if key.isnumeric()]
        cls.levels_available = levels_available

        cls.smithy_level = try_enum(UnitStat, smithy_levels)
        cls.level = cls.smithy_level and UnitStat(range(1, len(cls.smithy_level) + 1))
        cls.hero_level = try_enum(UnitStat,
                                  [json_meta.get(level).get("RequiredCharacterLevel") for level in levels_available])
        cls.speed = try_enum(UnitStat, [json_meta.get(level).get("Speed") for level in levels_available])
        cls.hitpoints = try_enum(UnitStat, [json_meta.get(level).get("HitPoints") for level in levels_available])
        cls.attack_range = try_enum(UnitStat, [json_meta.get(level).get("AttackRange") for level in levels_available])
        cls.dps = try_enum(UnitStat, [json_meta.get(level).get("DPS") for level in levels_available])
        cls.heal = try_enum(UnitStat, [json_meta.get(level).get("HealOnActivation") for level in levels_available])

        # hacky way to translate internal hero names to English
        hero = json_meta.get('AllowedCharacters', '').strip(';')
        hero_map = {"Warrior Princess": "Royal Champion", "Minion Hero": "Minion Prince"}
        cls.hero = hero_map.get(hero, hero)

        costs = [(int(el) for el in str(cost).split(';')) for cost in
                 [json_meta.get(level).get('UpgradeCosts') for level in levels_available] if cost]

        resources = [(Resource(el.strip()) for el in resource.split(';')) for resource in
                     [json_meta.get(level).get('UpgradeResources', '') for level in levels_available]]

        cls.upgrade_cost = try_enum(UnitStat, [[(c, r) for c, r in zip(cost, resource)]
                                               for cost, resource in zip(costs, resources)])

        cls._is_home_village = True  # todo: update with json key if they add builder base equipment
        cls.village = "home" if cls._is_home_village else "builderBase"

        cls.is_loaded = True
        return cls


class EquipmentHolder(DataContainerHolder):
    items: List[Type[Equipment]] = []
    item_lookup: Dict[str, Type[Equipment]]

    FILE_PATH = EQUIPMENT_FILE_PATH
    data_object = Equipment

    def _load_json(self, english_aliases, lab_to_townhall):
        id = 3000
        with open(EQUIPMENT_FILE_PATH) as fp:
            equipment_data = ujson.load(fp)

        for supercell_name, equipment_meta in equipment_data.items():
            if not equipment_meta.get("TID"):
                continue

            # ignore deprecated content
            if equipment_meta.get("Deprecated") or equipment_meta.get("DisableProduction"):
                continue

            new_equipment: Type[Equipment] = type('Equipment', Equipment.__bases__, dict(Equipment.__dict__))
            new_equipment._load_json_meta(
                equipment_meta,
                id=id,
                name=english_aliases[equipment_meta.get("TID")],
                smithy_to_townhall=lab_to_townhall,
            )
            id += 1
            self.items.append(new_equipment)
            self.item_lookup[new_equipment.name] = new_equipment

        self.is_loaded = True

    def load(self, data, townhall: int, default: "Equipment" = Equipment, load_game_data: bool = None
             ) -> Equipment:
        if load_game_data is True:
            try:
                equipment = self.item_lookup[data["name"]]
            except KeyError:
                equipment = default
        else:
            equipment = default

        return equipment(data=data, townhall=townhall)

    def get(self, name, home_village=True) -> Optional[Type[Equipment]]:
        try:
            return self.item_lookup[name]
        except KeyError:
            return None

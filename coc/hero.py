

from .abc import LeveledUnit
from .miscmodels import TimeDelta, TID
from .enums import Resource, VillageType, ProductionBuildingType, EquipmentRarity

class Hero(LeveledUnit):
    """Represents a Hero object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    name: :class:`str`
        The hero's name.
    village: :class:`VillageType`
        The village type (home or builder base) where this hero belongs.
    max_level: :class:`int`
        The maximum level this hero can be upgraded to.
    id: :class:`int`
        The hero's unique identifier.
    info: :class:`str`
        Description of the hero.
    TID: :class:`TID`
        The hero's translation IDs for localization.
    production_building: :class:`ProductionBuildingType`
        The building type that produces this hero.
    production_building_level: :class:`int`
        The required level of the production building to unlock this hero.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this hero.
    is_flying: :class:`bool`
        Whether this hero is an air unit.
    is_air_targeting: :class:`bool`
        Whether this hero can target air units.
    is_ground_targeting: :class:`bool`
        Whether this hero can target ground units.
    movement_speed: :class:`int`
        The hero's movement speed.
    attack_speed: :class:`int`
        The hero's attack speed.
    attack_range: :class:`int`
        The hero's attack range.
    hitpoints: :class:`int`
        The hero's hitpoints.
    dps: :class:`int`
        The hero's damage per second.
    upgrade_time: :class:`TimeDelta`
        The time required to upgrade to the next level.
    upgrade_cost: :class:`int`
        The cost to upgrade to the next level.
    required_hero_tavern_level: Optional[:class:`int`]
        The hero tavern level required to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    """

    __slots__ = (
        "name",
        "village",
        "max_level",
        "equipment",
        "id",
        "info",
        "TID",
        "production_building",
        "production_building_level",
        "upgrade_resource",
        "is_flying",
        "is_air_targeting",
        "is_ground_targeting",
        "movement_speed",
        "attack_speed",
        "attack_range",
        "hitpoints",
        "dps",
        "upgrade_time",
        "upgrade_cost",
        "required_hero_tavern_level",
        "required_townhall",
    )

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=data.get("level") or level,
            static_data=static_data
        )

        if data:
            self.name: str = data["name"]
            self.village = VillageType(value=data["village"])
            self.max_level: int = data["maxLevel"]
            self.equipment: list['Equipment'] = [
                Equipment(data=e, static_data=None) for e in data.get("equipment", [])
            ]

        if static_data:
            self.id: int = static_data["_id"]
            self.name: str = static_data["name"]
            self.info: str = static_data["info"]
            self.TID: TID = TID(data=static_data["TID"])

            self.production_building = ProductionBuildingType(value=str(static_data["production_building"]))
            self.production_building_level: int = static_data["production_building_level"] or 0
            self.upgrade_resource: Resource = Resource(value=static_data["upgrade_resource"])

            self.is_flying: bool = static_data["is_flying"]
            self.is_air_targeting: bool = static_data["is_air_targeting"]
            self.is_ground_targeting: bool = static_data["is_ground_targeting"]
            self.movement_speed: int = static_data["movement_speed"]
            self.attack_speed: int = static_data["attack_speed"]
            self.attack_range: int = static_data["attack_range"]

            self.village = VillageType(value=static_data["village"])

            self._load_level_data()

    def _load_level_data(self):
        if not self._static_data:
            return

        start_level = self._static_data["levels"][0]["level"]
        level_data = self._static_data["levels"][self._level - start_level]

        self.hitpoints: int = level_data["hitpoints"]
        self.dps: int = level_data["dps"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_hero_tavern_level: int | None = level_data["required_hero_tavern_level"]
        self.required_townhall: int = level_data["required_townhall"]


class Pet(LeveledUnit):
    """Represents a Pet object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    name: :class:`str`
        The pet's name.
    village: :class:`VillageType`
        The village type where this pet belongs.
    max_level: :class:`int`
        The maximum level this pet can be upgraded to.
    id: :class:`int`
        The pet's unique identifier.
    info: :class:`str`
        Description of the pet.
    TID: :class:`TID`
        The pet's translation IDs for localization.
    production_building: :class:`ProductionBuildingType`
        The building type that produces this pet.
    production_building_level: :class:`int`
        The required level of the production building to unlock this pet.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this pet.
    is_flying: :class:`bool`
        Whether this pet is an air unit.
    is_air_targeting: :class:`bool`
        Whether this pet can target air units.
    is_ground_targeting: :class:`bool`
        Whether this pet can target ground units.
    movement_speed: :class:`int`
        The pet's movement speed.
    attack_speed: :class:`int`
        The pet's attack speed.
    attack_range: :class:`int`
        The pet's attack range.
    hitpoints: :class:`int`
        The pet's hitpoints.
    dps: :class:`int`
        The pet's damage per second.
    upgrade_time: :class:`TimeDelta`
        The time required to upgrade to the next level.
    upgrade_cost: :class:`int`
        The cost to upgrade to the next level.
    required_pet_house_level: Optional[:class:`int`]
        The pet house level required to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    """

    __slots__ = (
        "name",
        "village",
        "max_level",
        "id",
        "info",
        "TID",
        "production_building",
        "production_building_level",
        "upgrade_resource",
        "is_flying",
        "is_air_targeting",
        "is_ground_targeting",
        "movement_speed",
        "attack_speed",
        "attack_range",
        "hitpoints",
        "dps",
        "upgrade_time",
        "upgrade_cost",
        "required_pet_house_level",
        "required_townhall",
    )

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=data.get("level") or level,
            static_data=static_data
        )

        if data:
            self.name: str = data["name"]
            self.village = VillageType(value=data["village"])
            self.max_level: int = data["maxLevel"]

        if static_data:
            self.id: int = static_data["_id"]
            self.name: str = static_data["name"]
            self.info: str = static_data["info"]
            self.TID: TID = TID(data=static_data["TID"])

            self.production_building = ProductionBuildingType(value=static_data["production_building"])
            self.production_building_level: int = static_data["production_building_level"] or 0
            self.upgrade_resource: Resource = Resource(value=static_data["upgrade_resource"])

            self.is_flying: bool = static_data["is_flying"]
            self.is_air_targeting: bool = static_data["is_air_targeting"]
            self.is_ground_targeting: bool = static_data["is_ground_targeting"]
            self.movement_speed: int = static_data["movement_speed"]
            self.attack_speed: int = static_data["attack_speed"]
            self.attack_range: int = static_data["attack_range"]

            self.village = VillageType.home

            self._load_level_data()

    def _load_level_data(self):
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.hitpoints: int = level_data["hitpoints"]
        self.dps: int = level_data["dps"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_pet_house_level: int | None = level_data["required_pet_house_level"]
        self.required_townhall: int = level_data["required_townhall"]


class Equipment(LeveledUnit):
    """Represents an Equipment object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    name: :class:`str`
        The equipment's name.
    village: :class:`VillageType`
        The village type where this equipment belongs.
    max_level: :class:`int`
        The maximum level this equipment can be upgraded to.
    id: :class:`int`
        The equipment's unique identifier.
    info: :class:`str`
        Description of the equipment.
    TID: :class:`TID`
        The equipment's translation IDs for localization.
    production_building: :class:`ProductionBuildingType`
        The building type that produces this equipment.
    production_building_level: :class:`int`
        The required level of the production building to unlock this equipment.
    rarity: :class:`EquipmentRarity`
        The rarity tier of this equipment.
    hero: :class:`str`
        The hero this equipment belongs to.
    hitpoints: :class:`int`
        The equipment's hitpoints bonus.
    dps: :class:`int`
        The equipment's damage per second bonus.
    heal_on_activation: :class:`int`
        The amount of healing provided when the equipment ability is activated.
    required_blacksmith_level: :class:`int`
        The blacksmith level required to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    shiny_ore: :class:`int`
        The amount of shiny ore required to upgrade to the next level.
    glowy_ore: :class:`int`
        The amount of glowy ore required to upgrade to the next level.
    starry_ore: :class:`int`
        The amount of starry ore required to upgrade to the next level.
    abilities: List[:class:`dict`]
        The list of abilities this equipment provides.
    """

    __slots__ = (
        "name",
        "village",
        "max_level",
        "id",
        "info",
        "TID",
        "production_building",
        "production_building_level",
        "rarity",
        "hero",
        "hitpoints",
        "dps",
        "heal_on_activation",
        "required_blacksmith_level",
        "required_townhall",
        "shiny_ore",
        "glowy_ore",
        "starry_ore",
        "abilities",
    )

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=data.get("level") or level,
            static_data=static_data
        )

        if data:
            self.name: str = data["name"]
            self.village = VillageType(value=data["village"])
            self.max_level: int = data["maxLevel"]

        if static_data:
            self.id: int = static_data["_id"]
            self.name: str = static_data["name"]
            self.info: str = static_data["info"]
            self.TID = TID(data=static_data["TID"])

            self.production_building = ProductionBuildingType(value=static_data["production_building"])
            self.production_building_level: int = static_data["production_building_level"] or 0

            self.rarity = EquipmentRarity(value=static_data["rarity"])
            self.hero: str = static_data["hero"]

            self.village = VillageType.home

            self._load_level_data()

    def _load_level_data(self):
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.hitpoints: int = level_data["hitpoints"]
        self.dps: int = level_data["dps"]
        self.heal_on_activation: int = level_data["heal_on_activation"]
        self.required_blacksmith_level: int = level_data["required_blacksmith_level"]
        self.required_townhall: int = level_data["required_townhall"]

        self.shiny_ore: int = level_data["upgrade_cost"]["shiny_ore"]
        self.glowy_ore: int = level_data["upgrade_cost"]["glowy_ore"]
        self.starry_ore: int = level_data["upgrade_cost"]["starry_ore"]

        self.abilities: list[dict] = level_data.get("abilities", [])

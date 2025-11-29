

from .abc import LeveledUnit
from .miscmodels import TimeDelta, TID
from .enums import Resource, VillageType, ProductionBuildingType, EquipmentRarity

class Hero(LeveledUnit):

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=level or data["level"],
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
            self.max_level: int = len(static_data["levels"])

            self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
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

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=level or data["level"],
            static_data=static_data
        )

        if data:
            self.name: str = data["name"]
            self.village = VillageType(value=["village"])
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
            self.max_level: int = len(static_data["levels"])

            self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
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

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=level or data["level"],
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

            self.max_level: int = len(static_data["levels"])
            self.village = VillageType.home

            self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
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


from .abc import LeveledUnit
from .enums import Resource, VillageType, ProductionBuildingType
from .miscmodels import TimeDelta, TID


class Troop(LeveledUnit):
    """Represents a Troop object as returned by the API, optionally filled with game data."""

    def __init__(self, data: dict, static_data: dict | None, level: int = 0):
        super().__init__(
            initial_level=level or data["level"],
            static_data=static_data
        )

        if data:
            self.name: str = data["name"]
            self.village = VillageType(value=data["village"])
            self.max_level: int = data["maxLevel"]
            self.is_active: bool = data.get("superTroopIsActive", False)

        if static_data:
            self.id: int = static_data["_id"]
            self.name: str = static_data["name"]
            self.info: str = static_data["info"]
            self.TID: TID = TID(data=static_data["TID"])

            self.production_building = ProductionBuildingType(value=static_data["production_building"])
            self.production_building_level: int = static_data["production_building_level"]
            self.upgrade_resource = Resource(value=static_data["upgrade_resource"])

            self.is_flying: bool = static_data["is_flying"]
            self.is_air_targeting: bool = static_data["is_air_targeting"]
            self.is_ground_targeting: bool = static_data["is_ground_targeting"]

            self.movement_speed: int = static_data["movement_speed"]
            self.attack_speed: int = static_data["attack_speed"]
            self.attack_range: int = static_data["attack_range"]
            self.housing_space: int = static_data["housing_space"]

            self.village = VillageType(value=static_data["village_type"])
            self.max_level = len(static_data["levels"])

            self.is_super_troop: bool = "super_troop" in static_data

            if self.is_super_troop:
                self.base_troop_id: int = static_data["super_troop"]["original_id"]
                self.base_troop_minimum_level: int = static_data["super_troop"]["original_min_level"]

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

        #is None for seasonal troops
        self.required_lab_level: int | None = level_data["required_lab_level"]
        self.required_townhall: int = level_data["required_townhall"]

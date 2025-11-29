
from .abc import LeveledUnit
from .enums import Resource, VillageType, ProductionBuildingType
from .miscmodels import TimeDelta, TID

class Spell(LeveledUnit):
    """Represents a Spell object as returned by the API, optionally filled with game data."""

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

            self.production_building = ProductionBuildingType(value=static_data["production_building"])
            self.production_building_level: int = static_data["production_building_level"]
            self.upgrade_resource = Resource(value=static_data["upgrade_resource"])

            self.housing_space: int = static_data["housing_space"]

            self.is_seasonal: bool = static_data.get("is_seasonal", False)

            self.village = VillageType.home
            self.max_level: int = len(static_data["levels"])

            self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.duration = TimeDelta(seconds=level_data["duration"])
        self.damage: int = level_data["damage"]
        self.radius: float = level_data["radius"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_lab_level: int = level_data["required_lab_level"]
        self.required_townhall: int = level_data["required_townhall"]
from .abc import LeveledUnit
from .enums import Resource, Gender
from .miscmodels import TID, TimeDelta


class Guardian(LeveledUnit):
    def __init__(self, level: int, data: dict | None):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.info: str = data["info"]
        self.TID: TID = TID(data=data["TID"])
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])
        self.is_flying: bool = data["is_flying"]
        self.is_air_targeting: bool = data["is_air_targeting"]
        self.is_ground_targeting: bool = data["is_ground_targeting"]
        self.movement_speed: int = data["movement_speed"]
        self.attack_speed: int = data["attack_speed"]
        self.attack_range: int = data["attack_range"]

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
        self.required_townhall: int = level_data["required_townhall"]


class Helper(LeveledUnit):
    def __init__(self, level: int, data: dict | None):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.gender = Gender(value=data["gender"])
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])

        self._load_level_data()


    def _load_level_data(self):
        """Load data specific to the current level."""
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_townhall: int = level_data["required_townhall"]
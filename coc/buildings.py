
from .abc import BaseDataClass, LeveledUnit, LevelManager
from .enums import Resource, VillageType, BuildingType
from .miscmodels import TID, TimeDelta


class SeasonalDefenseModule(LeveledUnit):
    def __init__(self, level: int, data: dict):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.upgrade_resource = Resource(value=data["upgrade_resource"])

        self.max_level: int = len(data["levels"])
        self._load_level_data()

    def _load_level_data(self):
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data.get("upgrade_cost")
        self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
        self.ability_data: dict = level_data.get("ability_data")

class SeasonalDefense(BaseDataClass):
    def __init__(self, data: dict, modules: list[SeasonalDefenseModule]):
        self.id = data["_id"]
        self.name: str = data["name"]
        self.info: str = data["info"]
        self.TID = TID(data=data["TID"])

        self.modules = modules
        self.level = sum(m.level for m in self.modules)

class MergeRequirement:
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.geared_up: bool = data["geared_up"]
        self.required_level: int = data["level"]

class GearUp:
    def __init__(self, data: dict):
        self.required_level: int = data["level_required"]
        self.building_id: int = data["building_id"]
        self.resource: Resource = Resource(value=data["resource"])

class TownhallUnlock:
    def __init__(self, data: dict):
        self.name: str = data["name"]
        self._id: int = data["_id"]
        self.quantity: int = data["quantity"]

class TownhallWeapon(LeveledUnit):
    def __init__(self, level: int, data: dict):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.name: str = data["name"]
        self.info: str = data["info"]
        self.TID: TID = TID(data=data["TID"])
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])

        self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.dps: int = level_data["dps"]

class Supercharge(LevelManager):
    def __init__(self, level: int, data: dict):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.name: str = data["name"]
        self.required_townhall: int = data["required_townhall"]
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])

        self._load_level_data()

    def _load_level_data(self):
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.hitpoints_buff: int = level_data["hitpoints_buff"]
        self.dps_buff: int = level_data["dps_buff"]

class Building(LeveledUnit):

    def __init__(self,
        level: int, data: dict, weapon_level: int = 0,
        supercharge_level: int = 0, supercharge_data: dict = None,
        seasonal_defenses: list[SeasonalDefense] = None
    ):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self._weapon_level = weapon_level
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.info: str = data["info"]
        self.TID: TID = TID(data=data["TID"])
        self.type = BuildingType(value=data["type"])
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])
        self.village = VillageType(value=data["village_type"])
        self.width: int = data["width"]
        self.is_superchargeable: bool = data["superchargeable"]

        if supercharge_data:
            self.supercharge = Supercharge(level=supercharge_level, data=supercharge_data)
        # only some buildings
        self.gear_up = None
        if "gear_up" in data:
            self.gear_up = GearUp(data=data["gear_up"])

        self.seasonal_defenses = seasonal_defenses or []

        self._load_level_data()

    def _load_level_data(self):
        """Load data specific to the current level."""
        if not self._static_data or not self._static_data["levels"]:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.weapon: TownhallWeapon | None = None
        if "weapon" in level_data:
            self.weapon = TownhallWeapon(level=self._weapon_level, data=level_data["weapon"])

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.required_townhall: int = level_data["required_townhall"]
        self.hitpoints: int = level_data["hitpoints"]
        self.dps: int = level_data["dps"]

        # only select buildings
        self.merge_requirement = [MergeRequirement(m) for m in level_data.get("merge_requirement", [])]

        # only the townhall
        self.unlocks = [TownhallUnlock(u) for u in level_data.get("unlocks", [])]

class Trap(LeveledUnit):

    def __init__(self, level: int, data: dict):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])

        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])
        self.village = VillageType(value=data["village_type"])
        self.width: int = data["width"]
        self.is_air_triggerable: bool = data["air_trigger"]
        self.is_ground_triggerable: bool = data["ground_trigger"]
        self.damage_radius: int = data["damage_radius"]
        self.trigger_radius: int = data["trigger_radius"]


    def _load_level_data(self):
        """Load data specific to the current level."""
        if not self._static_data or not self._static_data["levels"]:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.required_townhall: int = level_data["required_townhall"]
        self.damage: int = level_data["damage"]
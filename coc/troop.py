
from .abc import LeveledUnit
from .enums import Resource, VillageType, ProductionBuildingType
from .miscmodels import TimeDelta, TID


class Troop(LeveledUnit):
    """Represents a Troop object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    name: :class:`str`
        The troop's name.
    village: :class:`VillageType`
        The village type (home or builder base) where this troop belongs.
    is_home_base: :class:`bool`
        Whether this troop belongs to the home village.
    is_builder_base: :class:`bool`
        Whether this troop belongs to the builder base.
    max_level: :class:`int`
        The maximum level this troop can be upgraded to.
    is_active: :class:`bool`
        Whether this super troop is currently active/boosted.
    id: :class:`int`
        The troop's unique identifier.
    info: :class:`str`
        Description of the troop.
    TID: :class:`TID`
        The troop's translation IDs for localization.
    production_building: :class:`ProductionBuildingType`
        The building type that produces this troop.
    production_building_level: :class:`int`
        The required level of the production building to unlock this troop.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this troop.
    is_flying: :class:`bool`
        Whether this troop is an air unit.
    is_air_targeting: :class:`bool`
        Whether this troop can target air units.
    is_ground_targeting: :class:`bool`
        Whether this troop can target ground units.
    movement_speed: :class:`int`
        The troop's movement speed.
    attack_speed: :class:`int`
        The troop's attack speed.
    attack_range: :class:`int`
        The troop's attack range.
    housing_space: :class:`int`
        The housing space this troop occupies.
    is_super_troop: :class:`bool`
        Whether this is a super troop.
    is_seasonal: :class:`bool`
        Whether this is a seasonal/temporary troop.
    is_siege_machine: :class:`bool`
        Whether this is a siege machine.
    base_troop_id: :class:`int`
        The ID of the base troop (only for super troops).
    base_troop_minimum_level: :class:`int`
        The minimum level of the base troop required to boost this super troop.
    hitpoints: :class:`int`
        The troop's hitpoints.
    dps: :class:`int`
        The troop's damage per second.
    upgrade_time: :class:`TimeDelta`
        The time required to upgrade to the next level.
    upgrade_cost: :class:`int`
        The cost to upgrade to the next level.
    required_lab_level: Optional[:class:`int`]
        The laboratory level required to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    """

    __slots__ = (
        "name",
        "village",
        "is_home_base",
        "is_builder_base",
        "max_level",
        "is_active",
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
        "housing_space",
        "is_super_troop",
        "is_seasonal",
        "is_siege_machine",
        "base_troop_id",
        "base_troop_minimum_level",
        "hitpoints",
        "dps",
        "upgrade_time",
        "upgrade_cost",
        "required_lab_level",
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

            self.village = VillageType(value=static_data["village"])

            self.is_super_troop: bool = "super_troop" in static_data
            self.is_seasonal: bool = static_data.get("is_seasonal", False)
            self.is_siege_machine: bool = self.production_building == ProductionBuildingType.workshop

            if self.is_super_troop:
                self.base_troop_id: int = static_data["super_troop"]["original_id"]
                self.base_troop_minimum_level: int = static_data["super_troop"]["original_min_level"]

            self._load_level_data()

        self.is_home_base: bool = self.village == VillageType.home
        self.is_builder_base: bool = self.village == VillageType.builder_base

    def _load_level_data(self):
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


from .abc import LeveledUnit
from .enums import Resource, VillageType, ProductionBuildingType
from .miscmodels import TimeDelta, TID

class Spell(LeveledUnit):
    """Represents a Spell object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    name: :class:`str`
        The spell's name.
    village: :class:`VillageType`
        The village type (home or builder base) where this spell belongs.
    max_level: :class:`int`
        The maximum level this spell can be upgraded to.
    id: :class:`int`
        The spell's unique identifier.
    info: :class:`str`
        Description of the spell.
    TID: :class:`TID`
        The spell's translation IDs for localization.
    production_building: :class:`ProductionBuildingType`
        The building type that produces this spell.
    production_building_level: :class:`int`
        The required level of the production building to unlock this spell.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this spell.
    housing_space: :class:`int`
        The housing space this spell occupies.
    is_seasonal: :class:`bool`
        Whether this is a seasonal/temporary spell.
    duration: :class:`TimeDelta`
        The duration of the spell's effect.
    damage: :class:`int`
        The damage dealt by the spell.
    radius: :class:`float`
        The spell's area of effect radius.
    upgrade_time: :class:`TimeDelta`
        The time required to upgrade to this level.
    upgrade_cost: :class:`int`
        The cost to upgrade to this level.
    required_lab_level: :class:`int`
        The laboratory level required to upgrade to the next level.
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
        "housing_space",
        "is_seasonal",
        "duration",
        "damage",
        "radius",
        "upgrade_time",
        "upgrade_cost",
        "required_lab_level",
        "required_townhall",
    )

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
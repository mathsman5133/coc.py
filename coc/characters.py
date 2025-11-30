from .abc import LeveledUnit
from .enums import Resource
from .miscmodels import TID, TimeDelta


class Guardian(LeveledUnit):
    """Represents a Guardian character as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The guardian's unique identifier.
    name: :class:`str`
        The guardian's name.
    info: :class:`str`
        Description of the guardian.
    TID: :class:`TID`
        The guardian's translation IDs for localization.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this guardian.
    is_flying: :class:`bool`
        Whether this guardian is an air unit.
    is_air_targeting: :class:`bool`
        Whether this guardian can target air units.
    is_ground_targeting: :class:`bool`
        Whether this guardian can target ground units.
    movement_speed: :class:`int`
        The guardian's movement speed.
    attack_speed: :class:`int`
        The guardian's attack speed.
    attack_range: :class:`int`
        The guardian's attack range.
    hitpoints: :class:`int`
        The guardian's hitpoints.
    dps: :class:`int`
        The guardian's damage per second.
    upgrade_time: :class:`TimeDelta`
        The time required to upgrade to the next level.
    upgrade_cost: :class:`int`
        The cost to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    """

    __slots__ = (
        "id",
        "name",
        "info",
        "TID",
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
        "required_townhall",
    )

    def __init__(self, data: dict, level: int = 0):
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
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.hitpoints: int = level_data["hitpoints"]
        self.dps: int = level_data["dps"]
        self.upgrade_time = TimeDelta(seconds=level_data["upgrade_time"])
        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_townhall: int = level_data["required_townhall"]


class Helper(LeveledUnit):
    """Represents a Helper character as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The helper's unique identifier.
    name: :class:`str`
        The helper's name.
    TID: :class:`TID`
        The helper's translation IDs for localization.
    upgrade_resource: :class:`Resource`
        The resource type required to upgrade this helper.
    upgrade_cost: :class:`int`
        The cost to upgrade to the next level.
    required_townhall: :class:`int`
        The townhall level required to upgrade to the next level.
    """

    __slots__ = (
        "id",
        "name",
        "TID",
        "upgrade_resource",
        "upgrade_cost",
        "required_townhall",
    )

    def __init__(self, data: dict, level: int = 0):
        super().__init__(
            initial_level=level,
            static_data=data
        )
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.upgrade_resource: Resource = Resource(value=data["upgrade_resource"])

        self._load_level_data()


    def _load_level_data(self):
        if not self._static_data:
            return

        level_data = self._static_data["levels"][self._level - 1]

        self.upgrade_cost: int = level_data["upgrade_cost"]
        self.required_townhall: int = level_data["required_townhall"]
from .characters import Guardian, Helper
from .buildings import Trap, Building
from .cosmetics import Decoration, Obstacle, Skin, Scenery, ClanCapitalHousePart
from. hero import Hero, Pet, Equipment
from .troop import Troop
from .spell import Spell
from .abc import LeveledUnit
from .miscmodels import TimeDelta

class Upgrade:
    def __init__(self,
                 is_goblin: bool,
                 target: LeveledUnit,
                 timer: TimeDelta,
                 helper_timer: TimeDelta | None,
                 recurrent_helper: bool = False
                 ):
        self.is_goblin: bool = is_goblin
        self.target = target
        self.timer = timer
        self.helper_timer = helper_timer
        self.recurrent_helper = recurrent_helper

    def __repr__(self):
        attrs = [
            ("target", self.target.name if hasattr(self.target, "name") else "Unknown"),
            ("timer", self.timer),
            ("helper_timer", self.helper_timer),
            ("is_goblin", self.is_goblin),
            ("recurrent_helper", self.recurrent_helper),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs))

class Boosts:
    def __init__(self, data: dict = {}):
        self.builder_boost: TimeDelta = TimeDelta(seconds=data.get("builder_boost", 0))
        self.lab_boost: TimeDelta = TimeDelta(seconds=data.get("lab_boost", 0))
        self.clocktower_boost: TimeDelta = TimeDelta(seconds=data.get("clocktower_boost", 0))
        self.clocktower_cooldown: TimeDelta = TimeDelta(seconds=data.get("clocktower_cooldown", 0))
        self.builder_consumable: TimeDelta = TimeDelta(seconds=data.get("builder_consumable", 0))
        self.lab_consumable: TimeDelta = TimeDelta(seconds=data.get("lab_consumable", 0))
        self.helper_cooldown: TimeDelta = TimeDelta(seconds=data.get("helper_cooldown", 0))

    def __repr__(self):
        attrs = [
            ("builder_boost", self.builder_boost),
            ("lab_boost", self.lab_boost),
            ("clocktower_boost", self.clocktower_boost),
            ("clocktower_cooldown", self.clocktower_cooldown),
            ("builder_consumable", self.builder_consumable),
            ("lab_consumable", self.lab_consumable),
            ("helper_cooldown", self.helper_cooldown),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs))

class AccountData:
    def __init__(self):
        self.townhall_level: int = 0
        self.helpers: list[Helper] = []
        self.guardians: list[Guardian] = []
        self.buildings: list[tuple[Building, int]] = []
        self.traps: list[tuple[Trap, int]] = []
        self.decorations: list[tuple[Decoration, int]] = []
        self.obstacles: list[tuple[Obstacle, int]] = []
        self.troops: list[Troop] = []
        self.siege_machines: list[Troop] = []
        self.heroes: list[Hero] = []
        self.spells: list[Spell] = []
        self.pets: list[Pet] = []
        self.equipment: list[Equipment] = []
        self.capital_house_parts: list[ClanCapitalHousePart] = []
        self.skins: list[Skin] = []
        self.sceneries: list[Scenery] = []
        self.upgrades: list[Upgrade] = []
        self.boosts: Boosts = Boosts()

    def __repr__(self):
        attrs = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                attr_value = getattr(self, attr_name)
                if isinstance(attr_value, list):
                    attrs.append((attr_name, [repr(item) for item in attr_value]))
                else:
                    attrs.append((attr_name, repr(attr_value)))

        lines = [f"<{self.__class__.__name__}"]
        for name, value in attrs:
            lines.append(f"  {name}={value}")
        lines.append(">")
        return "\n".join(lines)
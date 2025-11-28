from .characters import Guardian, Helper
from .buildings import Trap, Building, SeasonalDefense, SeasonalDefenseModule
from .cosmetics import Decoration, Obstacle, Skin, Scenery, ClanCapitalHousePart
from. hero import Hero, Pet, Equipment
from .troop import Troop
from .spell import Spell
from .abc import LeveledUnit
from .miscmodels import TimeDelta
from .enums import BuildingType

import re

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from client import Client

TROOP_BASE_ID = 4000000
SPELL_BASE_ID = 26000000

HERO_BASE_ID = 28000000
PET_BASE_ID = 73000000
EQUIPMENT_BASE_ID = 90000000


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
    def __init__(self, data: dict, client: 'Client'):
        self._client = client
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

        self._load_data(data)

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

    def get_static_data_item(self, item_id: int | tuple[int, str]):
        item_data = self._client._static_data.get(item_id)
        return item_data

    def add_upgrade(self, item: dict, target: LeveledUnit) -> Upgrade | None:
        if "timer" in item:
            helper_timer = None
            if "helper_timer" in item:
                helper_timer = TimeDelta(seconds=item["helper_timer"])
            self.upgrades.append(
                Upgrade(
                    is_goblin=item.get("extra", False),
                    target=target,
                    timer=TimeDelta(seconds=item["timer"]),
                    helper_timer=helper_timer,
                    recurrent_helper=item.get("recurrent_helper", False)
                )
            )

    def _load_data(self, account_data: dict):
        self.boosts = Boosts(data=account_data.get("boosts", {}))

        # section is "guardians", "buildings", etc,
        for section, items in account_data.items():  # type: str, list[dict]

            if not isinstance(items, list) or "2" in section:
                continue
            # this adds builder base troops, heroes etc to the home village counterpart data/lists
            items.extend(account_data.get(f"{section}2", []))
            if section == "helpers":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    helper = Helper(
                        level=item.get("lvl", 0), data=item_data
                    )
                    if "helper_cooldown" in item:
                        self.boosts.helper_cooldown = TimeDelta(seconds=item["helper_cooldown"])
                    self.helpers.append(helper)

            elif section == "guardians":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    guardian = Guardian(
                        level=item.get("lvl"), data=item_data
                    )
                    self.add_upgrade(item, guardian)
                    self.guardians.append(guardian)

            elif section == "buildings":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    seasonal_defenses = []
                    if "types" in item:
                        crafting_station: list[dict] = item["types"]
                        for seasonal_defense in crafting_station:
                            seasonal_def_data = self.get_static_data_item(
                                item_id=seasonal_defense["data"]
                            )
                            modules = []
                            for module in seasonal_defense["modules"]:
                                module_data = next((
                                    item for item in seasonal_def_data["modules"] if item["_id"] == module["data"]
                                ))
                                modules.append(SeasonalDefenseModule(level=module["lvl"], data=module_data))
                                self.add_upgrade(item, module)
                            seasonal_defenses.append(SeasonalDefense(data=seasonal_def_data, modules=modules))

                    building = Building(
                        level=item.get("lvl", 0),
                        data=item_data,
                        weapon_level=item.get("weapon", 0),
                        supercharge_level=item.get("supercharge", 0),
                        seasonal_defenses=seasonal_defenses
                    )
                    if building.type == BuildingType.TOWN_HALL:
                        self.townhall_level = building.level
                    self.add_upgrade(item, building)
                    self.buildings.append((building, item.get("cnt", 1)))

            elif section == "traps":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    trap = Trap(
                        level=item.get("lvl"), data=item_data
                    )
                    self.add_upgrade(item, trap)
                    self.traps.append((trap, item.get("cnt", 1)))

            elif section == "decos":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    deco = Decoration(data=item_data)
                    self.decorations.append((deco, item.get("cnt", 1)))

            elif section == "obstacles":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    obstacle = Obstacle(data=item_data)
                    self.obstacles.append((obstacle, item.get("cnt", 1)))

            elif section == "units":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    troop = Troop(data={}, static_data=item_data, level=item["lvl"])
                    self.add_upgrade(item, troop)
                    self.troops.append(troop)

            elif section == "spells":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    spell = Spell(data={}, static_data=item_data, level=item["lvl"])
                    self.add_upgrade(item, spell)
                    self.spells.append(spell)

            elif section == "siege_machines":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    troop = Troop(data={}, static_data=item_data, level=item["lvl"])
                    self.add_upgrade(item, troop)
                    self.siege_machines.append(troop)

            elif section == "heroes":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    hero = Hero(data={}, static_data=item_data, level=item["lvl"])
                    self.add_upgrade(item, hero)
                    self.heroes.append(hero)

            elif section == "pets":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    pet = Pet(data={}, static_data=item_data, level=item["lvl"])
                    self.add_upgrade(item, pet)
                    self.pets.append(pet)

            elif section == "equipment":
                for item in items:
                    item_id = item["data"]
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    equipment = Equipment(data={}, static_data=item_data, level=item["lvl"])
                    self.equipment.append(equipment)

            elif section == "skins":
                for item_id in items:
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    skin = Skin(data=item_data)
                    self.skins.append(skin)

            elif section == "sceneries":
                for item_id in items:
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    scenery = Scenery(data=item_data)
                    self.sceneries.append(scenery)

            elif section == "house_parts":
                for item_id in items:
                    item_data = self.get_static_data_item(item_id=item_id)
                    if item_data is None:
                        continue
                    house_part = ClanCapitalHousePart(data=item_data)
                    self.capital_house_parts.append(house_part)


class HeroLoadout:
    def __init__(self, loadout: tuple, lookup):

        self._lookup = lookup

        self.hero: Hero = self._lookup.get(loadout[0], HERO_BASE_ID)
        self.pet: Pet | None = self._lookup.get(loadout[1], PET_BASE_ID) if loadout[1] else None
        self.equipment: list[Equipment] = []
        for e in loadout[2:]:
            if e:
                self.equipment.append(self._lookup.equipment.get(e, EQUIPMENT_BASE_ID))


class ArmyRecipe:
    def __init__(self, static_data: dict, link: str):
        self.link = link

        self._lookup = static_data
        self.__heroes = []
        self.__castle_troops = []
        self.__castle_spells = []
        self.__units = []
        self.__spells = []

        self.heroes_loadout: list[HeroLoadout] = []
        self.troops: list[tuple[Troop, int]] = []
        self.spells: list[tuple[Spell, int]] = []
        self.clan_castle_troops: list[tuple[Troop, int]] = []
        self.clan_castle_spells: list[tuple[Spell, int]] = []

        self._parse()

    def _parse_items(self, match_str: str, base_id: int, item_class, target_list: list):
        """Helper to parse troops or spells from army link."""
        for split in (item.split('x') for item in match_str.split('-')):
            item_id = int(split[1]) + base_id
            quantity = int(split[0])
            static_data = self._lookup.get(item_id, self._lookup.get(base_id))
            item = item_class(data={}, static_data=static_data, level=1)
            target_list.append((item, quantity))

    def _parse(self):

        ARMY_LINK_SEPARATOR = re.compile(
            r"h(?P<heroes>[^idus]+)"
            r"|i(?P<castle_troops>[\d+x-]+)"
            r"|d(?P<castle_spells>[\d+x-]+)"
            r"|u(?P<units>[\d+x-]+)"
            r"|s(?P<spells>[\d+x-]+)"
        )

        # Regex to parse an individual hero entry.
        # - hero_id is required.
        # - pet_id (prefixed by "p") is optional.
        # - Equipment (prefixed by "e") is optional; if present, eq1 is required, eq2 (after an underscore) is optional.
        hero_pattern = re.compile(
            r"(?P<hero_id>\d+)"
            r"(?:m\d+)?"
            r"(?:p(?P<pet_id>\d+))?"
            r"(?:e(?P<eq1>\d+)(?:_(?P<eq2>\d+))?)?"
        )

        # Iterate over all section matches.
        for match in ARMY_LINK_SEPARATOR.finditer(self.link):
            if match.group("heroes"):
                hero_entries = match.group("heroes").split('-')
                for hero in hero_entries:
                    m = hero_pattern.fullmatch(hero)
                    if m:
                        hero_id = HERO_BASE_ID + int(m.group("hero_id"))
                        pet_id = PET_BASE_ID + int(m.group("pet_id")) if m.group("pet_id") else None
                        eq1 = EQUIPMENT_BASE_ID + int(m.group("eq1")) if m.group("eq1") else None
                        eq2 = EQUIPMENT_BASE_ID + int(m.group("eq2")) if m.group("eq2") else None
                        self.heroes_loadout.append(HeroLoadout((hero_id, pet_id, eq1, eq2), self._lookup))

            elif match.group("castle_troops"):
                self._parse_items(match.group("castle_troops"), TROOP_BASE_ID, Troop, self.clan_castle_troops)

            elif match.group("castle_spells"):
                self._parse_items(match.group("castle_spells"), SPELL_BASE_ID, Spell, self.clan_castle_spells)

            elif match.group("units"):
                self._parse_items(match.group("units"), TROOP_BASE_ID, Troop, self.troops)

            elif match.group("spells"):
                self._parse_items(match.group("spells"), SPELL_BASE_ID, Spell, self.spells)

        self._lookup = None
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
    """Represents an ongoing upgrade.

    Attributes
    ----------
    is_goblin: :class:`bool`
        Whether this is a goblin builder upgrade.
    target: :class:`LeveledUnit`
        The target item being upgraded.
    timer: :class:`TimeDelta`
        The time remaining for the upgrade.
    helper_timer: Optional[:class:`TimeDelta`]
        The time remaining for the helper boost.
    recurrent_helper: :class:`bool`
        Whether the helper is recurrent.
    """

    __slots__ = (
        "is_goblin",
        "target",
        "timer",
        "helper_timer",
        "recurrent_helper",
    )

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
    """Represents active boosts and cooldowns.

    Attributes
    ----------
    builder_boost: :class:`TimeDelta`
        The time remaining for the builder potion boost.
    lab_boost: :class:`TimeDelta`
        The time remaining for the research potion boost.
    clocktower_boost: :class:`TimeDelta`
        The time remaining for the clock tower boost.
    clocktower_cooldown: :class:`TimeDelta`
        The cooldown time for the clock tower.
    builder_consumable: :class:`TimeDelta`
        The time remaining for the builder bite snack.
    lab_consumable: :class:`TimeDelta`
        The time remaining for the study soup snack.
    helper_cooldown: :class:`TimeDelta`
        The global cooldown timer for helpers.
    """

    __slots__ = (
        "builder_boost",
        "lab_boost",
        "clocktower_boost",
        "clocktower_cooldown",
        "builder_consumable",
        "lab_consumable",
        "helper_cooldown",
    )

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


class StaticData:
    """Represents static game data loaded from game files.
    
    This class loads and organizes all static game data from the game's data files.
    It provides access to all available game items at all levels, useful for looking
    up item information, max levels, and statistics.
    
    Attributes
    ----------
    buildings: List[:class:`Building`]
        List of all available buildings.
    capital_house_parts: List[:class:`ClanCapitalHousePart`]
        List of all available clan capital house parts.
    decorations: List[:class:`Decoration`]
        List of all available decorations.
    equipment: List[:class:`Equipment`]
        List of all available equipment.
    guardians: List[:class:`Guardian`]
        List of all available guardians.
    helpers: List[:class:`Helper`]
        List of all available helpers.
    heroes: List[:class:`Hero`]
        List of all available heroes.
    obstacles: List[:class:`Obstacle`]
        List of all available obstacles.
    pets: List[:class:`Pet`]
        List of all available pets.
    sceneries: List[:class:`Scenery`]
        List of all available sceneries.
    skins: List[:class:`Skin`]
        List of all available skins.
    spells: List[:class:`Spell`]
        List of all available spells.
    traps: List[:class:`Trap`]
        List of all available traps.
    troops: List[:class:`Troop`]
        List of all available troops & siege machines.
    """
    
    __slots__ = (
        "_data",
        "helpers",
        "guardians",
        "buildings",
        "traps",
        "decorations",
        "obstacles",
        "troops",
        "siege_machines",
        "heroes",
        "spells",
        "pets",
        "equipment",
        "capital_house_parts",
        "skins",
        "sceneries",
    )
    
    def __init__(self, data: dict):
        self._data = data

        self.buildings: list[Building] = []
        self.capital_house_parts: list[ClanCapitalHousePart] = []
        self.decorations: list[Decoration] = []
        self.equipment: list[Equipment] = []
        self.guardians: list[Guardian] = []
        self.helpers: list[Helper] = []
        self.heroes: list[Hero] = []
        self.obstacles: list[Obstacle] = []
        self.pets: list[Pet] = []
        self.sceneries: list[Scenery] = []
        self.skins: list[Skin] = []
        self.spells: list[Spell] = []
        self.traps: list[Trap] = []
        self.troops: list[Troop] = []

        self._load_data()

    def _load_data(self):

        section_class_mapping = {
            "helpers": Helper,
            "buildings": Building,
            "traps": Trap,
            "troops": Troop,
            "guardians": Guardian,
            "spells": Spell,
            "heroes": Hero,
            "pets": Pet,
            "equipment": Equipment,
            "decorations": Decoration,
            "obstacles": Obstacle,
            "sceneries": Scenery,
            "skins": Skin,
            "capital_house_parts": ClanCapitalHousePart,
        }
        for section, items in self._data.items():
            cls = section_class_mapping.get(section)
            if cls is None:
                continue

            for item in items:
                data = item
                if section in ["troops", "spells", "heroes", "pets", "equipment"]:
                    static_data = item
                    data = {}
                    self.__getattribute__(section).append(cls(data=data, static_data=static_data))
                else:
                    self.__getattribute__(section).append(cls(data=data))


class AccountData:
    """Represents player account data parsed from game files.
    
    Parses raw account data from game files and creates game objects representing
    the player's village state, including buildings, troops, heroes, ongoing upgrades,
    and active boosts. This provides a complete snapshot of a player's account.

    Attributes
    ----------
    townhall_level: :class:`int`
        The player's current townhall level.
    buildings: List[Tuple[:class:`Building`, :class:`int`]]
        Player's buildings as tuples of (building, quantity). Buildings can have multiple
        instances (e.g., multiple cannons).
    capital_house_parts: List[:class:`ClanCapitalHousePart`]
        Player's unlocked clan capital house parts.
    decorations: List[Tuple[:class:`Decoration`, :class:`int`]]
        Player's decorations as tuples of (decoration, quantity).
    equipment: List[:class:`Equipment`]
        Player's equipment with their current levels.
    guardians: List[:class:`Guardian`]
        Player's guardians with their current levels.
    helpers: List[:class:`Helper`]
        Player's helpers with their current levels.
    heroes: List[:class:`Hero`]
        Player's heroes with their current levels.
    obstacles: List[Tuple[:class:`Obstacle`, :class:`int`]]
        Player's obstacles as tuples of (obstacle, quantity).
    pets: List[:class:`Pet`]
        Player's pets with their current levels.
    sceneries: List[:class:`Scenery`]
        Player's unlocked base sceneries.
    skins: List[:class:`Skin`]
        Player's unlocked hero skins.
    spells: List[:class:`Spell`]
        Player's unlocked spells with their current levels.
    traps: List[Tuple[:class:`Trap`, :class:`int`]]
        Player's traps as tuples of (trap, quantity).
    troops: List[:class:`Troop`]
        Player's unlocked troops with their current levels.
    upgrades: List[:class:`Upgrade`]
        Currently ongoing upgrades (buildings, troops, spells, heroes, etc.).
    boosts: :class:`Boosts`
        Active boosts and cooldowns (builder boost, lab boost, clock tower, etc.).
    """

    __slots__ = (
        "_client",
        "townhall_level",
        "helpers",
        "guardians",
        "buildings",
        "traps",
        "decorations",
        "obstacles",
        "troops",
        "heroes",
        "spells",
        "pets",
        "equipment",
        "capital_house_parts",
        "skins",
        "sceneries",
        "upgrades",
        "boosts",
    )

    def __init__(self, data: dict, client: 'Client'):
        self._client = client
        self.townhall_level: int = 0

        self.buildings: list[tuple[Building, int]] = []
        self.capital_house_parts: list[ClanCapitalHousePart] = []
        self.decorations: list[tuple[Decoration, int]] = []
        self.equipment: list[Equipment] = []
        self.guardians: list[Guardian] = []
        self.helpers: list[Helper] = []
        self.heroes: list[Hero] = []
        self.obstacles: list[tuple[Obstacle, int]] = []
        self.pets: list[Pet] = []
        self.sceneries: list[Scenery] = []
        self.skins: list[Skin] = []
        self.spells: list[Spell] = []
        self.traps: list[tuple[Trap, int]] = []
        self.troops: list[Troop] = []
        self.upgrades: list[Upgrade] = []

        self.boosts: Boosts = Boosts()

        self._load_data(account_data=data)

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
                            seasonal_def_data = next((
                                item for item in item_data["seasonal_defenses"]
                                if item["_id"] == seasonal_defense["data"]
                            ))
                            if seasonal_def_data is None:
                                continue
                            modules = []
                            for module in seasonal_defense["modules"]:
                                module_data = next((
                                    item for item in seasonal_def_data["modules"] if item["_id"] == module["data"]
                                ))
                                if module_data is None:
                                    continue
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
                    if building.type == BuildingType.town_hall:
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

            elif section == "units" or section == "siege_machines":
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
    """Represents a hero loadout from an army link.

    Attributes
    ----------
    hero: :class:`Hero`
        The hero in this loadout.
    pet: Optional[:class:`Pet`]
        The pet assigned to this hero.
    equipment: List[:class:`Equipment`]
        The list of equipment assigned to this hero.
    """

    __slots__ = (
        "_lookup",
        "hero",
        "pet",
        "equipment",
    )

    def __init__(self, loadout: tuple, lookup):

        self._lookup = lookup

        self.hero: Hero = Hero(
            data={}, level=1,
            static_data=self._lookup.get(loadout[0], self._lookup.get(HERO_BASE_ID))
        )
        self.pet = None
        if loadout[1]:
            self.pet: Pet | None = Pet(
                data={}, level=1,
                static_data=self._lookup.get(loadout[1], self._lookup.get(PET_BASE_ID))
            )
        self.equipment: list[Equipment] = []
        for e in loadout[2:]:
            if e:
                self.equipment.append(
                    Equipment(
                        data={}, level=1,
                        static_data=self._lookup.get(e, self._lookup.get(EQUIPMENT_BASE_ID)))
                    )


class ArmyRecipe:
    """Represents an army composition parsed from an army link.

    Attributes
    ----------
    link: :class:`str`
        The army link string.
    heroes_loadout: List[:class:`HeroLoadout`]
        The list of hero loadouts.
    troops: List[Tuple[:class:`Troop`, :class:`int`]]
        The list of troops with their quantities.
    spells: List[Tuple[:class:`Spell`, :class:`int`]]
        The list of spells with their quantities.
    clan_castle_troops: List[Tuple[:class:`Troop`, :class:`int`]]
        The list of clan castle troops with their quantities.
    clan_castle_spells: List[Tuple[:class:`Spell`, :class:`int`]]
        The list of clan castle spells with their quantities.
    """

    __slots__ = (
        "link",
        "_lookup",
        "heroes_loadout",
        "troops",
        "spells",
        "clan_castle_troops",
        "clan_castle_spells",
    )

    def __init__(self, static_data: dict, link: str):
        self.link = link

        self._lookup = static_data

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
"""
MIT License

Copyright (c) 2019-2020 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import ujson
from pathlib import Path
from typing import AsyncIterator, Any, Dict, Type, Optional, TYPE_CHECKING

from .enums import PETS_ORDER, Resource
from .miscmodels import try_enum, Badge, TimeDelta
from .iterators import PlayerIterator
from .utils import CaseInsensitiveDict, UnitStat, _get_maybe_first

if TYPE_CHECKING:
    from .players import Player

BUILDING_FILE_PATH = Path(__file__).parent.joinpath(
    Path("static/buildings.json"))


class BaseClan:
    """
    Abstract data class that represents base Clan objects

    Attributes
    ----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    """
    __slots__ = ("tag", "name", "_client", "badge", "level", "_response_retry", "_raw_data")

    def __init__(self, *, data, client, **kwargs):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.badge = try_enum(Badge, data=data.get("badgeUrls"),
                              client=self._client)
        self.level = data.get("clanLevel")
        self._raw_data = data if client and client.raw_attribute else None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} tag={self.tag} name={self.name}>"

    def __eq__(self, other):
        return isinstance(other, BaseClan) and self.tag == other.tag

    @property
    def share_link(self) -> str:
        """str: A formatted link to open the clan in-game"""
        return f"https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{self.tag.strip('#')}"

    @property
    def members(self):
        # pylint: disable=missing-function-docstring
        return NotImplemented

    def get_detailed_members(self, cls: Type["Player"] = None,
                             load_game_data: bool = None) -> AsyncIterator["Player"]:
        """Get detailed player information for every player in the clan.

        This returns a :class:`PlayerIterator` which fetches all player
        tags in the clan in parallel.

        Example
        ---------

        .. code-block:: python3

            clan = await client.get_clan(clan_tag)

            async for player in clan.get_detailed_members():
                print(player.name)


        Yields
        ------
        :class:`Player`
            A full player object of a clan member.
        """
        if self.members is NotImplemented:
            return NotImplemented
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        return PlayerIterator(self._client,
                              (p.tag for p in self.members),
                              cls=cls,
                              load_game_data=load_game_data,
                              members=self.members_dict)


class BasePlayer:
    """An ABC that implements some common operations on players, regardless of type.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    """

    __slots__ = ("tag", "name", "_client", "_response_retry", "_raw_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} tag={self.tag} name={self.name}>"

    def __eq__(self, other):
        return isinstance(other, BasePlayer) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")
        self._raw_data = data if client and client.raw_attribute else None
        self.tag = data.get("tag")
        self.name = data.get("name")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the player in-game"""
        return f"https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{self.tag.strip('#')}"


class DataContainerMetaClass(type):
    pass


class DataContainer(metaclass=DataContainerMetaClass):
    lab_to_townhall: Dict[int, int]
    name: str

    def __init__(self, data, townhall):
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]
        self.is_active: bool = data.get("superTroopIsActive")

        self._townhall = townhall

        # copies for a static hash
        self.__name = data['name']
        self.__level = data['level']
        self.__village = data['village']
        self.__is_active = data.get("superTroopIsActive")

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("level", self.level),
            ("is_active", self.is_active),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return self.name == other.name and self.level == other.level \
            and self.village == other.village and self.is_active == other.is_active

    def __hash__(self):
        return hash((self.__name, self.__level, self.__village, self.__is_active))

    @classmethod
    def _load_json_meta(cls, json_meta, id, name, lab_to_townhall):
        cls.id = int(id)
        cls.name = name
        cls.lab_to_townhall = lab_to_townhall

        cls.range = try_enum(UnitStat, json_meta.get("AttackRange"))
        cls.dps = try_enum(UnitStat, json_meta.get("DPS"))
        cls.ground_target = _get_maybe_first(json_meta, "GroundTargets",
                                             default=True)
        cls.hitpoints = try_enum(UnitStat, json_meta.get("Hitpoints"))

        # get production building
        production_building = json_meta.get("ProductionBuilding", [None])[0] if json_meta.get("ProductionBuilding") else None
        if production_building == "Barrack":
            cls.is_elixir_troop = True
        elif production_building == "Dark Elixir Barrack":
            cls.is_dark_troop = True
        elif production_building == "SiegeWorkshop":
            cls.is_siege_machine = True
        elif production_building == "Spell Forge":
            cls.is_elixir_spell = True
        elif production_building == "Mini Spell Factory":
            cls.is_dark_spell = True
        elif name in PETS_ORDER:
            production_building = "Pet Shop"

        # load buildings
        with open(BUILDING_FILE_PATH) as fp:
            buildings = ujson.load(fp)

        # without production_building, it is a hero
        if not production_building:
            laboratory_levels = json_meta.get("LaboratoryLevel")
        else:
            # it is a troop or spell or siege
            prod_unit = buildings.get(production_building)
            if production_building in ("SiegeWorkshop", "Spell Forge", "Mini Spell Factory",
                                       "Dark Elixir Barrack", "Barrack", "Barrack2"):
                min_prod_unit_level = json_meta.get("BarrackLevel", [None, ])[0]
                # there are some special troops, which have no BarrackLevel attribute
                if not min_prod_unit_level:
                    laboratory_levels = json_meta.get("LaboratoryLevel")
                else:
                    # get the min th level were we can unlock by the required level of the production building
                    min_th_level = [th for i, th in
                                    enumerate(prod_unit["TownHallLevel"], start=1)
                                    if i == min_prod_unit_level]
                    # map the min th level to a lab level
                    [first_lab_level] = [lab_level for lab_level, th_level in
                                         lab_to_townhall.items()
                                         if th_level in min_th_level]
                    # the first_lab_level is the lowest possible (there are some inconsistencies with siege machines)
                    # To handle them properly, replacing all lab_level lower than first_lab_level with first_lab_level
                    laboratory_levels = []
                    for lab_level in json_meta.get("LaboratoryLevel"):
                        laboratory_levels.append(max(lab_level, first_lab_level))
            elif production_building == "Pet Shop":
                min_prod_unit_level = json_meta.get("LaboratoryLevel", [None, ])[0]
                # there are some special troops, which have no BarrackLevel attribute

                # get the min th level were we can unlock by the required level of the production building
                min_th_level = [th for i, th in
                                enumerate(prod_unit["TownHallLevel"], start=1)
                                if i == min_prod_unit_level]
                # map the min th level to a lab level
                [first_lab_level] = [lab_level for lab_level, th_level in
                                     lab_to_townhall.items()
                                     if th_level in min_th_level]
                # the first_lab_level is the lowest possible (there are some inconsistencies with siege machines)
                # To handle them properly, replacing all lab_level lower than first_lab_level with first_lab_level
                laboratory_levels = []
                for lab_level in json_meta.get("LaboratoryLevel"):
                    laboratory_levels.append(max(lab_level, first_lab_level))
            else:
                return

        cls.lab_level = try_enum(UnitStat, laboratory_levels)
        cls.housing_space = _get_maybe_first(json_meta, "HousingSpace", default=0)
        cls.speed = try_enum(UnitStat, json_meta.get("Speed"))
        cls.level = cls.dps and UnitStat(range(1, len(cls.dps) + 1))

        # all 3
        cls.upgrade_cost = try_enum(UnitStat, json_meta.get("UpgradeCost"))
        cls.upgrade_resource = Resource(value=json_meta["UpgradeResource"][0])
        cls.upgrade_time = try_enum(UnitStat,
                                    [TimeDelta(hours=hours) for hours in
                                     json_meta.get("UpgradeTimeH", [])])
        cls._is_home_village = False if json_meta.get("VillageType") else True
        cls.village = "home" if cls._is_home_village else "builderBase"

        # spells and troops
        cls.training_cost = try_enum(UnitStat, json_meta.get("TrainingCost"))
        cls.training_time = try_enum(UnitStat, json_meta.get("TrainingTime"))

        # only heroes
        cls.ability_time = try_enum(UnitStat, json_meta.get("AbilityTime"))
        cls.ability_troop_count = try_enum(UnitStat, json_meta.get("AbilitySummonTroopCount"))
        cls.required_th_level = try_enum(UnitStat, json_meta.get("RequiredTownHallLevel") or laboratory_levels)
        cls.regeneration_time = try_enum(
            UnitStat, [TimeDelta(minutes=value) for value in json_meta.get("RegenerationTimeMinutes", [])]
        )

        cls.is_loaded = True
        return cls

    @property
    def is_max(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop is the max level"""
        return self.max_level == self.level

    @property
    def is_builder_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop belongs to the builder base."""
        return self.village == "builderBase"

    @property
    def is_home_base(self) -> bool:
        """:class:`bool`: Returns a boolean that indicates whether the troop belongs to the home base."""
        return self.village == "home"

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "maxLevel": self.max_level,
            "village": self.village,
            "is_active": self.is_active,
        }

    def _load_from_parent(self, parent: Type["DataContainer"]):
        for k, v in parent.__dict__.items():
            if "__" not in k:
                setattr(self.__class__, k, v)


class DataContainerHolder:
    items = NotImplemented
    item_lookup: CaseInsensitiveDict = CaseInsensitiveDict()

    FILE_PATH = NotImplemented
    data_object = NotImplemented

    def __init__(self):
        self.loaded = False

    def _load_json(self, english_aliases, lab_to_townhall):
        with open(self.FILE_PATH) as fp:
            data = ujson.load(fp)

        id = 2000
        for c, [supercell_name, meta] in enumerate(data.items()):

            # Not interested if it doesn't have a TID, since it likely isn't a real troop.
            if not meta.get("TID"):
                continue

            # Some duplication with tutorial goblins and barbs which we don't care about
            if "Tutorial" in supercell_name:
                continue

            # SC game files have "DisableProduction" true for all pet objects, which we want
            if True in meta.get("DisableProduction", [False]) and "pets" not in str(self.FILE_PATH):
                continue

            # ignore deprecated content
            if True in meta.get("Deprecated", [False]):
                continue

            #hacky but the aliases convert so that isnt great
            IGNORED_PETS = ["Unused", "PhoenixEgg"]
            if "pets" in str(self.FILE_PATH) and supercell_name in IGNORED_PETS:
                continue

            # A bit of a hacky way to create a "copy" of a new Troop object that hasn't been initiated yet.
            new_item = type(self.data_object.__name__,
                            self.data_object.__bases__,
                            dict(self.data_object.__dict__))
            new_item._load_json_meta(
                meta,
                id=id,
                name=english_aliases[meta["TID"][0]]["EN"][0],
                lab_to_townhall=lab_to_townhall,
            )
            id += 1
            self.items.append(new_item)
            self.item_lookup[new_item.name] = new_item

        self.loaded = True

    def load(
            self, data: dict, townhall: int, default: Type[DataContainer] = None,
            load_game_data: bool = True) -> DataContainer:
        if load_game_data is True:
            try:
                item = self.item_lookup[data["name"]]
            except KeyError:
                item = default or self.data_object
        else:
            item = default or self.data_object

        return item(data=data, townhall=townhall)

    def get(self, name: str) -> Optional[Type[DataContainer]]:
        try:
            return self.item_lookup[name]
        except KeyError:
            return None

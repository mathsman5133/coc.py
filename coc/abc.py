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

from typing import AsyncIterator, Any, Dict, Type, Optional, TYPE_CHECKING

from .enums import Resource
from .miscmodels import try_enum, Badge, TimeDelta
from .iterators import PlayerIterator
from .utils import CaseInsensitiveDict, UnitStat, _get_maybe_first

if TYPE_CHECKING:
    from .players import Player


class BaseClan:
    """An ABC that implements some common operations on clans, regardless of type.

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

    __slots__ = ("tag", "name", "_client", "badge", "level", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % (self.__class__.__name__, self.tag, self.name)

    def __eq__(self, other):
        return isinstance(other, BaseClan) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.badge = try_enum(Badge, data=data.get("badgeUrls"), client=self._client)
        self.level = data.get("clanLevel")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the clan in-game"""
        return "https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{}".format(self.tag.strip("#"))

    @property
    def members(self):
        # pylint: disable=missing-function-docstring
        return NotImplemented

    def get_detailed_members(self, cls: Type["Player"] = None, load_game_data: bool = None) -> AsyncIterator["Player"]:
        """Get detailed player information for every player in the clan.

        This returns a :class:`PlayerIterator` which fetches all player tags in the clan in parallel.

        Example
        ---------

        .. code-block:: python3

            clan = await client.get_clan('tag')

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

        return PlayerIterator(self._client, (p.tag for p in self.members), cls=cls, load_game_data=load_game_data)


class BasePlayer:
    """An ABC that implements some common operations on players, regardless of type.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    """

    __slots__ = ("tag", "name", "_client", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % (self.__class__.__name__, self.tag, self.name,)

    def __eq__(self, other):
        return isinstance(other, BasePlayer) and self.tag == other.tag

    def __init__(self, *, data, client, **_):
        self._client = client
        self._response_retry = data.get("_response_retry")

        self.tag = data.get("tag")
        self.name = data.get("name")

    @property
    def share_link(self) -> str:
        """:class:`str` - A formatted link to open the player in-game"""
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))


class DataContainerMetaClass(type):
    def __repr__(cls):
        attrs = [
            ("name", cls.name),
            ("id", cls.id),
        ]
        return "<%s %s>" % (cls.__name__, " ".join("%s=%r" % t for t in attrs),)


class DataContainer(metaclass=DataContainerMetaClass):
    lab_to_townhall: Dict[int, int]

    def __init__(self, data, townhall):
        self.name: str = data["name"]
        self.level: int = data["level"]
        self.max_level: int = data["maxLevel"]
        self.village: str = data["village"]
        self.is_active: bool = data.get("superTroopIsActive")

        self._townhall = townhall

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("level", self.level),
            ("is_active", self.is_active),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    @classmethod
    def _load_json_meta(cls, troop_meta, id, name, lab_to_townhall):
        cls.id = int(id)
        cls.name = name
        cls.lab_to_townhall = lab_to_townhall

        cls.range = try_enum(UnitStat, troop_meta.get("AttackRange"))
        cls.dps = try_enum(UnitStat, troop_meta.get("DPS"))
        cls.ground_target = _get_maybe_first(troop_meta, "GroundTargets", default=True)
        cls.hitpoints = try_enum(UnitStat, troop_meta.get("Hitpoints"))

        cls.housing_space = _get_maybe_first(troop_meta, "HousingSpace", default=0)
        cls.lab_level = try_enum(UnitStat, troop_meta.get("LaboratoryLevel"))
        cls.speed = try_enum(UnitStat, troop_meta.get("Speed"))
        cls.level = cls.dps and UnitStat(range(1, len(cls.dps) + 1))

        # all 3
        cls.upgrade_cost = try_enum(UnitStat, troop_meta.get("UpgradeCost"))
        cls.upgrade_resource = Resource(value=troop_meta["UpgradeResource"][0])
        cls.upgrade_time = try_enum(UnitStat, [TimeDelta(hours=hours) for hours in troop_meta.get("UpgradeTimeH", [])])
        cls._is_home_village = False if troop_meta.get("VillageType") else True

        # spells and troops
        cls.training_cost = try_enum(UnitStat, troop_meta.get("TrainingCost"))
        cls.training_resource = Resource(value=troop_meta["TrainingResource"][0])
        cls.training_time = try_enum(UnitStat, troop_meta.get("TrainingTime"))

        # only heroes
        cls.ability_time = try_enum(UnitStat, troop_meta.get("AbilityTime"))
        cls.ability_troop_count = try_enum(UnitStat, troop_meta.get("AbilitySummonTroopCount"))
        cls.required_th_level = try_enum(UnitStat, troop_meta.get("RequiredTownHallLevel"))
        cls.regeneration_time = try_enum(UnitStat, [TimeDelta(minutes=value) for value in troop_meta.get("RegenerationTimeMinutes", [])])

        production_building = troop_meta.get("ProductionBuilding", [None])[0]
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

    def _load_json(self, object_ids, english_aliases, lab_to_townhall):
        with open(self.FILE_PATH) as fp:
            data = ujson.load(fp)

        for supercell_name, meta in data.items():
            # Not interested if it doesn't have a TID, since it likely isn't a real troop.
            if not meta.get("TID"):
                continue

            # Some duplication with tutorial goblins and barbs which we don't care about
            if "Tutorial" in supercell_name:
                continue

            # SC game files have "DisableProduction" true for all pet objects, which we want
            if "DisableProduction" in meta and "pets" not in str(self.FILE_PATH):
                continue

            # Little bit of a hacky way to create a "copy" of a new Troop object that hasn't been initiated yet.
            new_item = type(self.data_object.__name__, self.data_object.__bases__, dict(self.data_object.__dict__))
            new_item._load_json_meta(
                meta,
                id=object_ids.get(supercell_name, 0),
                name=english_aliases[meta["TID"][0]][0],
                lab_to_townhall=lab_to_townhall,
            )

            self.items.append(new_item)
            self.item_lookup[new_item.name] = new_item

        self.loaded = True

    def load(
        self, data, townhall: int, default: Type[DataContainer] = None, load_game_data: bool = True
    ) -> DataContainer:
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

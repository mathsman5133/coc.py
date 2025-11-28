
from .abc import BaseDataClass
from .enums import Resource, PlayerHouseElementType, VillageType
from .miscmodels import TID


class Decoration(BaseDataClass):
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.width: int = data["width"]
        self.in_shop: bool = not data["not_in_shop"]
        self.pass_reward: bool = data["pass_reward"]
        self.max_count: int = data["max_count"]
        self.build_resource: Resource = Resource(value=data["build_resource"])
        self.build_cost: int = data["build_cost"]
        self.village_type = VillageType(value=data["village_type"])

class Obstacle(BaseDataClass):
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.width: int = data["width"]
        self.clear_resource = Resource(value=data["clear_resource"])
        self.clear_cost: int = data["clear_cost"]
        self.loot_resource : Resource | None = Resource(value=data["loot_resource"]) if "loot_resource" in data else None
        self.loot_count: int | None = data["loot_count"]
        self.village_type = VillageType(value=data["village_type"])

class Scenery(BaseDataClass):
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.type: str = data["type"]
        self.has_music: bool = data["music"] is not None

class Skin(BaseDataClass):
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.tier: str = data["tier"]
        self.hero: str = data["character"]

class ClanCapitalHousePart(BaseDataClass):
    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.slot_type = PlayerHouseElementType(value=data["slot_type"])
        self.pass_reward: bool = data["pass_reward"]


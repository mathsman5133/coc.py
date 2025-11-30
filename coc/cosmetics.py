
from .abc import BaseDataClass
from .enums import Resource, PlayerHouseElementType, VillageType, SceneryType
from .miscmodels import TID


class Decoration(BaseDataClass):
    """Represents a Decoration.

    Attributes
    ----------
    id: :class:`int`
        The decoration's unique identifier.
    name: :class:`str`
        The decoration's name.
    TID: :class:`TID`
        The decoration's translation IDs for localization.
    width: :class:`int`
        The width of the decoration.
    in_shop: :class:`bool`
        Whether this decoration is available in the shop.
    pass_reward: :class:`bool`
        Whether this decoration is a pass reward.
    max_count: :class:`int`
        The maximum number of this decoration that can be placed.
    shop_resource: :class:`Resource`
        The resource type required to buy this decoration.
    cost: :class:`int`
        The cost to buy/place this decoration.
    village: :class:`VillageType`
        The village type where this decoration belongs.
    """

    __slots__ = (
        "id",
        "name",
        "TID",
        "width",
        "in_shop",
        "pass_reward",
        "max_count",
        "shop_resource",
        "cost",
        "village",
    )

    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.width: int = data["width"]
        self.in_shop: bool = not data["not_in_shop"]
        self.pass_reward: bool = data["pass_reward"]
        self.max_count: int = data["max_count"]
        self.shop_resource: Resource = Resource(value=data["build_resource"])
        self.cost: int = data["build_cost"]
        self.village = VillageType(value=data["village"])

class Obstacle(BaseDataClass):
    """Represents an Obstacle.

    Attributes
    ----------
    id: :class:`int`
        The obstacle's unique identifier.
    name: :class:`str`
        The obstacle's name.
    TID: :class:`TID`
        The obstacle's translation IDs for localization.
    width: :class:`int`
        The width of the obstacle.
    clear_resource: :class:`Resource`
        The resource type required to clear this obstacle.
    clear_cost: :class:`int`
        The cost to clear this obstacle.
    loot_resource: Optional[:class:`Resource`]
        The resource type obtained from clearing this obstacle.
    loot_count: Optional[:class:`int`]
        The amount of loot obtained from clearing this obstacle.
    village: :class:`VillageType`
        The village type where this obstacle belongs.
    """

    __slots__ = (
        "id",
        "name",
        "TID",
        "width",
        "clear_resource",
        "clear_cost",
        "loot_resource",
        "loot_count",
        "village",
    )

    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.width: int = data["width"]
        self.clear_resource = Resource(value=data["clear_resource"])
        self.clear_cost: int = data["clear_cost"]
        self.loot_resource : Resource | None = data["loot_resource"] and Resource(value=data["loot_resource"])
        self.loot_count: int | None = data["loot_count"]
        self.village = VillageType(value=data["village"])

class Scenery(BaseDataClass):
    """Represents a Scenery.

    Attributes
    ----------
    id: :class:`int`
        The scenery's unique identifier.
    name: :class:`str`
        The scenery's name.
    TID: :class:`TID`
        The scenery's translation IDs for localization.
    village: :class:`SceneryType`
        The scenery type.
    has_music: :class:`bool`
        Whether this scenery has custom music.
    """

    __slots__ = (
        "id",
        "name",
        "TID",
        "village",
        "has_music",
    )

    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.village = SceneryType(value=data["type"])
        self.has_music: bool = data["music"] is not None

class Skin(BaseDataClass):
    """Represents a Hero Skin.

    Attributes
    ----------
    id: :class:`int`
        The skin's unique identifier.
    name: :class:`str`
        The skin's name.
    TID: :class:`TID`
        The skin's translation IDs for localization.
    tier: :class:`str`
        The tier/rarity of the skin.
    hero: :class:`str`
        The hero this skin belongs to.
    """

    __slots__ = (
        "id",
        "name",
        "TID",
        "tier",
        "hero",
    )

    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.TID: TID = TID(data=data["TID"])
        self.tier: str = data["tier"]
        self.hero: str = data["character"]

class ClanCapitalHousePart(BaseDataClass):
    """Represents a Clan Capital House Part.

    Attributes
    ----------
    id: :class:`int`
        The house part's unique identifier.
    name: :class:`str`
        The house part's name.
    slot_type: :class:`PlayerHouseElementType`
        The type of house element slot.
    pass_reward: :class:`bool`
        Whether this house part is a pass reward.
    """

    __slots__ = (
        "id",
        "name",
        "slot_type",
        "pass_reward",
    )

    def __init__(self, data: dict):
        self.id: int = data["_id"]
        self.name: str = data["name"]
        self.slot_type = PlayerHouseElementType(value=data["slot_type"])
        self.pass_reward: bool = data["pass_reward"]


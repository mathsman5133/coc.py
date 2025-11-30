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

__version__ = "4.0.0"

from .abc import BasePlayer, BaseClan
from .buildings import (
    Building,
    GearUp,
    MergeRequirement,
    SeasonalDefenseModule,
    SeasonalDefense,
    Supercharge,
    TownhallUnlock,
    TownhallWeapon,
    Trap,
)
from .characters import Guardian, Helper
from .clans import RankedClan, Clan
from .client import Client
from .constants import *
from .cosmetics import Skin, Scenery, Obstacle, Decoration, ClanCapitalHousePart
from .events import PlayerEvents, ClanEvents, WarEvents, EventsClient, ClientEvents
from .enums import (
    PlayerHouseElementType,
    Resource,
    Role,
    WarRound,
    WarState,
    BattleModifier,
    WarResult,
    ProductionBuildingType,
    BuildingType,
    VillageType,
    SceneryType,
    EquipmentRarity,
    SkinTier,
    Gender,
    UNRANKED_LEAGUE_DATA,
)
from .errors import (
    ClashOfClansException,
    HTTPException,
    NotFound,
    InvalidArgument,
    InvalidCredentials,
    Forbidden,
    Maintenance,
    GatewayError,
    PrivateWarLog,
)
from .game_data import AccountData, Upgrade, Boosts, ArmyRecipe, HeroLoadout, StaticData
from .hero import Equipment, Hero, Pet
from .http import BasicThrottler, BatchThrottler, HTTPClient
from .iterators import (
    ClanIterator,
    ClanWarIterator,
    PlayerIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .miscmodels import (
    Achievement,
    Badge,
    BaseLeague,
    CapitalDistrict,
    ChatLanguage,
    GoldPassSeason,
    Icon,
    Label,
    League,
    LegendStatistics,
    LoadGameData,
    Location,
    PlayerHouseElement,
    Season,
    Timestamp,
    TimeDelta,
    TID,
    Translation
)
from .players import Player, ClanMember, RankedPlayer
from .player_clan import PlayerClan
from .raid import RaidClan, RaidMember, RaidLogEntry, RaidDistrict, RaidAttack
from .spell import Spell
from .troop import Troop
from .war_clans import WarClan, ClanWarLeagueClan
from .war_attack import WarAttack
from .war_members import ClanWarLeagueClanMember, ClanWarMember
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup, ExtendedCWLGroup
from . import utils

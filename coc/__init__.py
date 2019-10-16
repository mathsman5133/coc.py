# -*- coding: utf-8 -*-

__version__ = '0.3.0'

from .cache import (
    Cache,
    CacheConfig,
    DefaultCache,
    MaxSizeCache,
    TimeToLiveCache
)

from .clans import (
    Clan,
    SearchClan,
    BasicClan,
    WarClan,
    LeagueClan
)
from .client import Client, login
from .events import EventsClient
from .enums import (
    CacheType,
    HOME_TROOP_ORDER,
    BUILDER_TROOPS_ORDER,
    SPELL_ORDER,
    HERO_ORDER,
    SIEGE_MACHINE_ORDER
)
from .errors import (
    ClashOfClansException,
    HTTPException,
    NotFound,
    InvalidArgument,
    InvalidCredentials,
    Forbidden,
    Maitenance,
    GatewayError,
    PrivateWarLog
)
from .http import HTTPClient
from .iterators import (
    ClanIterator,
    PlayerIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator
)
from .miscmodels import (
    Achievement,
    Badge,
    EqualityComparable,
    Hero,
    League,
    LegendStatistics,
    Location,
    Spell,
    Troop,
    Timestamp,
    Label

)
from .players import (
    Player,
    BasicPlayer,
    SearchPlayer,
    LeaguePlayer,
    LeagueRankedPlayer,
    WarMember
)
from .wars import (
    BaseWar,
    WarLog,
    ClanWar,
    WarAttack,
    LeagueGroup,
    LeagueWar,
    LeagueWarLogEntry
)
from . import utils


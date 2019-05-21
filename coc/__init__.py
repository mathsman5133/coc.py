# -*- coding: utf-8 -*-

__version__ = '0.2.0a'

from .clans import (
    Clan,
    SearchClan,
    BasicClan,
    WarClan,
    LeagueClan
)
from .client import Client, login
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
    GatewayError
)
from .http import HTTPClient
from .iterators import (
    ClanIterator,
    PlayerIterator,
    WarIterator
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
    CurrentWar,
    WarAttack,
    LeagueGroup,
    LeagueWar,
    LeagueWarLogEntry
)




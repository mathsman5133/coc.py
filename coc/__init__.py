# -*- coding: utf-8 -*-

__version__ = '0.2.1'

from .clans import (
    Clan,
    SearchClan,
    BasicClan,
    WarClan,
    LeagueClan
)
from .client import Client, EventsClient, login
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




# -*- coding: utf-8 -*-

__version__ = '0.1.2'

from .client import Client
from .dataclasses import (
    Clan,
    BasicClan,
    SearchClan,
    WarClan,
    Player,
    BasicPlayer,
    WarMember,
    SearchPlayer,
    BaseWar,
    WarLog,
    CurrentWar,
    Achievement,
    Troop,
    Hero,
    Spell,
    WarAttack,
    Location,
    League,
    LeagueRankedPlayer,
    Season,
    LegendStatistics,
    Badge,
    Timestamp,
    LeaguePlayer,
    LeagueClan,
    LeagueGroup,
    LeagueWar,
    LeagueWarLogEntry
)
from .errors import (
    ClashOfClansException,
    HTTPException,
    NotFound,
    InvalidArgument,
    InvalidCredentials,
    Forbidden,
    Maitenance
)
from .http import HTTPClient

from .enums import (
    CacheType
)

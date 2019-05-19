# -*- coding: utf-8 -*-

__version__ = '0.2.0a'

from .client import Client, login
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

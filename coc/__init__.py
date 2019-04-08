# -*- coding: utf-8 -*-

__version__ = '0.0.1'

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
    Acheivement,
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
    LeagueWar
)
from .errors import (
    ClashOfClansException,
    HTTPException,
    NotFound,
    InvalidArgument,
    InvalidToken,
    Maitenance
)
from .http import HTTPClient

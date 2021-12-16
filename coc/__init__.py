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

__version__ = "2.0.0"

from .abc import BasePlayer, BaseClan
from .clans import RankedClan, Clan
from .client import Client
from .events import PlayerEvents, ClanEvents, WarEvents, EventsClient, ClientEvents
from .enums import (
    Resource,
    Role,
    WarRound,
    ACHIEVEMENT_ORDER,
    BUILDER_TROOPS_ORDER,
    HERO_ORDER,
    HERO_PETS_ORDER,
    HOME_TROOP_ORDER,
    SIEGE_MACHINE_ORDER,
    SPELL_ORDER,
    SUPER_TROOP_ORDER,
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
from .login import login, login_with_keys
from .hero import Hero, Pet
from .http import BasicThrottler, BatchThrottler, HTTPClient
from .iterators import (
    ClanIterator,
    PlayerIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .miscmodels import (
    Achievement,
    Badge,
    Icon,
    League,
    LegendStatistics,
    LoadGameData,
    Location,
    Timestamp,
    TimeDelta,
    Label,
    WarLeague,
)
from .players import Player, ClanMember, RankedPlayer
from .player_clan import PlayerClan
from .spell import Spell
from .troop import Troop
from .war_clans import WarClan, ClanWarLeagueClan
from .war_attack import WarAttack
from .war_members import ClanWarLeagueClanMember, ClanWarMember
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup
from . import utils

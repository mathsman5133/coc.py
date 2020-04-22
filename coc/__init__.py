"""
Clash of Clans API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Clash of Clans API.

:copyright: (c) 2015-2019 mathsman5133
:license: MIT, see LICENSE for more details.

"""
__version__ = "0.3.4"

from .cache import Cache, CacheConfig, DefaultCache, MaxSizeCache, TimeToLiveCache

from .clans import Clan, SearchClan, BasicClan, WarClan, LeagueClan
from .client import Client
from .events import EventsClient
from .enums import (
    CacheType,
    Role,
    ACHIEVEMENT_ORDER,
    BUILDER_TROOPS_ORDER,
    DARK_ELIXIR_SPELL_ORDER,
    DARK_ELIXIR_TROOP_ORDER,
    ELIXIR_SPELL_ORDER,
    ELIXIR_TROOP_ORDER,
    HERO_ORDER,
    HOME_TROOP_ORDER,
    SIEGE_MACHINE_ORDER,
    SPELL_ORDER,
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
from .login import login
from .http import HTTPClient
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
    EqualityComparable,
    Hero,
    League,
    LegendStatistics,
    Location,
    Spell,
    Troop,
    Timestamp,
    Label,
    WarLeague,
)
from .players import (
    Player,
    BasicPlayer,
    SearchPlayer,
    LeaguePlayer,
    LeagueRankedPlayer,
    WarMember,
)
from .wars import (
    BaseWar,
    WarLog,
    ClanWar,
    WarAttack,
    LeagueGroup,
    LeagueWar,
    LeagueWarLogEntry,
)
from . import utils

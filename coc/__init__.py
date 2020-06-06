"""
Clash of Clans API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Clash of Clans API.

:copyright: (c) 2015-2019 mathsman5133
:license: MIT, see LICENSE for more details.

"""
__version__ = "0.3.3"


from .clans import *
from .client import Client
from .events import *
from .enums import (
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
    Hero,
    League,
    LegendStatistics,
    Location,
    Spell,
    Troop,
    Timestamp,
    Label,
)
from .players import Player
from .war_clans import WarClan, ClanWarLeagueClan
from .war_attack import WarAttack
from .war_members import ClanWarLeagueClanMember, ClanWarMember
from .wars import *
from . import utils

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
import asyncio
import logging
from enum import Enum

from itertools import cycle
from pathlib import Path
from typing import AsyncIterator, Iterable, List, Optional, Type, Union, TYPE_CHECKING

import ujson

from .clans import Clan, RankedClan
from .errors import Forbidden, GatewayError, NotFound, PrivateWarLog
from .enums import WarRound
from .miscmodels import BaseLeague, GoldPassSeason, Label, League, Location, LoadGameData
from .hero import HeroHolder, PetHolder, EquipmentHolder
from .http import HTTPClient, BasicThrottler, BatchThrottler
from .iterators import (
    PlayerIterator,
    ClanIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .players import Player, ClanMember, RankedPlayer
from .raid import RaidLogEntry
from .spell import SpellHolder
from .troop import TroopHolder
from .utils import correct_tag, get, parse_army_link
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup
from .entry_logs import ClanWarLog, RaidLog

if TYPE_CHECKING:
    from .hero import Hero, Pet, Equipment
    from .spell import Spell
    from .troop import Troop


LOG = logging.getLogger(__name__)

LEAGUE_WAR_STATE = "notInWar"
KEY_MINIMUM, KEY_MAXIMUM = 1, 10

ENGLISH_ALIAS_PATH = Path(__file__).parent.joinpath(Path("static/texts_EN.json"))
BUILDING_FILE_PATH = Path(__file__).parent.joinpath(Path("static/buildings.json"))


class ClashAccountScopes(Enum):
    """
    Values represent the scope required for each type of user. A USER is
    anyone who has access to the API. A REAL user is a user with special
    access from SuperCell with realtime scope access.
    """
    USER = "clash"
    REAL = "clash:*:verifytoken,realtime"


class Client:
    """This is the client connection used to interact with the Clash of Clans API.

    Parameters
    ----------
    key_count : int
        The amount of keys to use for this client. Maximum of 10.
        Defaults to 1.

    key_names : str
        Default name for keys created to use for this client.
        All keys created or to be used with this client must
        have this name.
        Defaults to "Created with coc.py Client".

    throttle_limit : int
        The number of requests per token per second to send to the API.
        Once hitting this limit, the library will automatically throttle
        your requests.

        .. note::

            Setting this value too high may result in the API rate-limiting
            your requests. This means you cannot request for ~30-60 seconds.

        .. warning::

            Setting this value too high may result in your requests being
            deemed "API Abuse", potentially resulting in an IP ban.

        Defaults to 10 requests per token, per second.

    loop : :class:`asyncio.AbstractEventLoop`, optional
        The :class:`asyncio.AbstractEventLoop` to use for HTTP requests.
        An :func:`asyncio.get_event_loop()` will be used if ``None`` is passed

    correct_tags : :class:`bool`
        Whether the client should correct tags before requesting them from the API.
        This process involves stripping tags of whitespace and adding a `#` prefix if not present.
        Defaults to ``True``.

    connector : :class:`aiohttp.BaseConnector`
        The aiohttp connector to use. By default, this is ``None``.

    timeout: :class:`float`
        The number of seconds before timing out with an API query. Defaults to 30.

    cache_max_size: :class:`int`
        The max size of the internal cache layer. Defaults to 10 000. Set this to ``None`` to remove any cache layer.

    load_game_data: :class:`LoadGameData`
        The option for how coc.py will load game data. See :ref:`initialising_game_data` for more info.

    realtime: :class:`bool`
        Some developers are given special access to an uncached API access by
        Super Cell. If you are one of those developers, your account will have
        special flags that will only be interpreted by coc.py if you set this
        bool to True.

    raw_attribute: :class:`bool`
        The option to enable the _raw_data attribute for most objects in the library. This attribute will contain
        the original json data as returned by the API. This can be useful if you want to store a response in a database
        for later use or are interested in new things that coc.py does not support otherwise yet. But because this
        increases the memory footprint and is not needed for most use cases, this defaults to ``False``.

    base_url: :class:`str`
        The base URL to use for API requests. Defaults to "https://api.clashofclans.com/v1"

    ip: :class:`str`
        The IP address to use for API requests. Defaults to None, which means the IP address will be automatically
        detected.
        
    lookup_cache: :class:`bool`
        Flag for controlling the cache usage before an actual API request is made. Defaults to True, which means the cache lookup is done
    
    update_cache: :class:`bool`
        Flag for controlling if the cache is updated after an API request was made. Defaults to True, which means the cache is updated
        after an API request.
    
    ignore_cached_errors: :class:`list[int]`
        In case of a cache lookup and a cached entry exists, ignore the cached data if the status code of the response is in the list.
    
    player_cls: :class:`Type[Player]`
        Class to be used for player objects. Defaults to :class:`Player`.
    
    member_cls: :class:`Type[ClanMember]`
        Class to be used for clan member objects. Defaults to :class:`ClanMember`.
    
    ranke
    
    clan_cls: :class:`Type[Clan]`
        Class to be used for clan objects. Defaults to :class:`Clan`.
    

    Attributes
    ----------
    loop : :class:`asyncio.AbstractEventLoop`
        The loop that is used for HTTP requests
    """

    __slots__ = (
        "base_url",
        "ip",
        "loop",
        "correct_key_count",
        "key_names",
        "key_scopes",
        "throttle_limit",
        "throttler",
        "timeout",
        "connector",
        "cache_max_size",
        "stats_max_size",
        "http",
        "realtime",
        "raw_attribute",
        "_ready",
        "correct_tags",
        "load_game_data",
        "lookup_cache",
        "update_cache",
        "ignore_cached_errors",
        "_players",
        "_clans",
        "_wars",
        "objects_cls",
        "_troop_holder",
        "_spell_holder",
        "_hero_holder",
        "_pet_holder",
        "_equipment_holder"
    )

    def __init__(
        self,
        *,
        key_count: int = 1,
        key_names: str = "Created with coc.py Client",
        throttle_limit: int = 30,
        loop: asyncio.AbstractEventLoop = None,
        correct_tags: bool = True,
        throttler: Type[Union[BasicThrottler, BatchThrottler]] = BasicThrottler,
        connector=None,
        timeout: float = 30.0,
        cache_max_size: int = 10000,
        stats_max_size: int = 1000,
        load_game_data: LoadGameData = LoadGameData(default=True),
        realtime=False,
        raw_attribute=False,
        base_url: str = "https://api.clashofclans.com/v1",
        ip: Optional[str] = None,
        lookup_cache: Optional[bool] = True,
        update_cache: Optional[bool] = True,
        ignore_cached_errors: Union[List[int], None] = None,
        **kwargs,
    ):

        self.loop = loop or asyncio.get_event_loop()

        self.correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == self.correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(KEY_MINIMUM, KEY_MAXIMUM))

        self.key_names = key_names
        self.key_scopes = ClashAccountScopes.REAL.value if realtime else ClashAccountScopes.USER.value
        self.throttle_limit = throttle_limit
        self.throttler = throttler
        self.connector = connector
        self.timeout = timeout
        self.cache_max_size = cache_max_size
        self.stats_max_size = stats_max_size
        
        self.lookup_cache = lookup_cache
        self.update_cache = update_cache
        self.ignore_cached_errors = ignore_cached_errors

        self.http: Optional[HTTPClient] = None  # set in method login()
        self.realtime = realtime
        self.raw_attribute = raw_attribute
        self.correct_tags = correct_tags
        self.load_game_data = load_game_data
        self.base_url = base_url
        self.ip = ip
        
        self.objects_cls = {"Player": Player, "Clan": Clan, "ClanWar": ClanWar,
                            "RankedPlayer": RankedPlayer, "RankedClan": RankedClan,
                            "ClanMember": ClanMember, "ClanWarLogEntry": ClanWarLogEntry, "RaidLogEntry": RaidLogEntry,
                            "ClanWarLeagueGroup": ClanWarLeagueGroup, "Location": Location,
                            "League": League, "BaseLeague": BaseLeague, "GoldPassSeason": GoldPassSeason,
                            "Label": Label}
        
        # cache
        self._players = {}
        self._clans = {}
        self._wars = {}

    @property
    def _defaults(self):
        return {
            "lookup_cache": self.lookup_cache,
            "update_cache": self.update_cache,
            "ignore_cached_errors": self.ignore_cached_errors,
            "realtime": self.realtime,
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
        
    def set_object_cls(self, name: str, cls):
        """Set a custom class type for a given object name. The method ensures that the
        provided class is a valid subclass of a predefined default class. It updates
        the internal mapping of object classes to the new custom class.
        
        .. note::
        
            This affects only the return type of Client methods returning the object.
            For example changing the ClanMember class to a custom class will affect 'get_clan_members', but not the clan members
            of a clan object obtained by calling `get_clan` or `get_clans` methods.

        Parameters
        -----------
        name: str
            The name of the object whose class type is to be set. It must be one of
            the predefined object types such as "Player", "Clan", etc.
        cls:
            The custom class type to be associated with the given object name. The
            class must be a subclass of the corresponding default class type.

        Raises
        -------
        ValueError
            If the provided object name is not supported.
        TypeError
            If the provided class is not a subclass of the default class for the given
            object name.
        """
        default_cls = {"Player": Player, "Clan": Clan, "ClanWar": ClanWar,
                       "RankedPlayer": RankedPlayer, "RankedClan": RankedClan,
                       "ClanMember": ClanMember, "ClanWarLogEntry": ClanWarLogEntry, "RaidLogEntry": RaidLogEntry,
                       "ClanWarLeagueGroup": ClanWarLeagueGroup, "Location": Location,
                       "League": League, "BaseLeague": BaseLeague, "GoldPassSeason": GoldPassSeason,
                       "Label": Label}
        if name not in default_cls:
            raise ValueError(f"Setting a cls with the name {name} is not supported.")
        if not issubclass(cls, default_cls[name]):
            raise TypeError(f"The cls {cls} must be a subclass of {default_cls[name]}")
        self.objects_cls[name] = cls

    def _create_client(self, email, password):
        return HTTPClient(
            client=self,
            email=email,
            password=password,
            key_names=self.key_names,
            key_scopes=self.key_scopes,
            loop=self.loop,
            key_count=self.correct_key_count,
            throttle_limit=self.throttle_limit,
            throttler=self.throttler,
            cache_max_size=self.cache_max_size,
            stats_max_size=self.stats_max_size,
            base_url=self.base_url,
            ip=self.ip,
            lookup_cache=self.lookup_cache,
            update_cache=self.update_cache,
            ignore_cached_errors=self.ignore_cached_errors,
        )

    def _load_holders(self):
        with open(ENGLISH_ALIAS_PATH) as fp:
            english_aliases = ujson.load(fp)

        with open(BUILDING_FILE_PATH) as fp:
            buildings = ujson.load(fp)

        english_aliases = {
            v["TID"]: v.get("EN", None)
            for outer_dict in english_aliases.values()
            for v in outer_dict.values()
        }

        # defaults for if loading fails
        lab_to_townhall = {i - 2: i for i in range(1, 17)}
        smithy_to_townhall = {i - 7: i for i in range(8, 17)}

        for supercell_name, data in buildings.items():
            if supercell_name == "Laboratory":
                lab_to_townhall = {int(lab_level): level_data.get("TownHallLevel")
                                   for lab_level, level_data in data.items() if lab_level.isnumeric()}
                # there are troops with no lab ...
                lab_to_townhall[-1] = 1
                lab_to_townhall[0] = 2
            elif supercell_name =='Smithy':
                smithy_to_townhall = {int(lab_level): level_data.get("TownHallLevel")
                                   for lab_level, level_data in data.items() if lab_level.isnumeric()}

        # load holders tied to the lab
        for holder in (self._troop_holder, self._spell_holder, self._hero_holder, self._pet_holder):
            holder._load_json(english_aliases, lab_to_townhall)
        # load holders tied to the smithy
        self._equipment_holder._load_json(english_aliases, smithy_to_townhall)

    def _create_holders(self):
        self._troop_holder = TroopHolder()
        self._spell_holder = SpellHolder()
        self._hero_holder = HeroHolder()
        self._pet_holder = PetHolder()
        self._equipment_holder = EquipmentHolder()

        if not self.load_game_data.never:
            self._load_holders()

    async def login(self, email: str, password: str) -> None:
        """Retrieves all keys and creates an HTTP connection ready for use.

        Parameters
        ----------
        email : str
            Your password email from https://developer.clashofclans.com
            This is used when updating keys automatically if your IP changes

        password : str
            Your password login from https://developer.clashofclans.com
            This is used when updating keys automatically if your IP changes
        """
        self.http = http = self._create_client(email, password)
        await http.create_session(self.connector, self.timeout)
        await http.initialise_keys()

        self._create_holders()
        LOG.debug("HTTP connection created. Client is ready for use.")

    def login_with_keys(self, *keys: str) -> None:
        """Creates an HTTP connection ready for use with the keys you provide.

        .. deprecated:: v2.3.0
            This function has been deemed deprecated to allow
            asyncio to clean up the async structures. Please use :func:`Client.login_with_tokens`
            instead.

        Parameters
        ----------
        keys: list[str]
            Keys or tokens as found from https://developer.clashofclans.com.


        """
        self.correct_key_count = len(keys)
        self.http = http = self._create_client(None, None)
        http._keys = keys
        http.keys = cycle(http._keys)
        self.loop.run_until_complete(http.create_session(self.connector, self.timeout))
        self._create_holders()

        LOG.debug("HTTP connection created. Client is ready for use.")

    async def login_with_tokens(self, *tokens: str) -> None:
        """Creates an HTTP connection ready for use with the tokens you provide.

        Parameters
        ----------
        tokens: list[str]
            Tokens as found from https://developer.clashofclans.com under "My account" -> <your key> -> "token".
        """
        self.correct_key_count = len(tokens)
        self.http = http = self._create_client(None, None)
        http._keys = tokens
        http.keys = cycle(http._keys)
        await http.create_session(self.connector, self.timeout)
        self._create_holders()

        LOG.debug("HTTP connection created. Client is ready for use.")

    async def close(self) -> None:
        """Closes the HTTP connection from within a loop function such as
        async def main()"""
        await self.http.close()

    def dispatch(self, event_name: str, *args, **kwargs) -> None:
        """Dispatches an event listener matching the `event_name` parameter."""
        LOG.debug("Dispatching %s event", event_name)

        try:
            fctn = getattr(self, event_name)
        except AttributeError:
            return

        if asyncio.iscoroutinefunction(fctn):
            self.loop.create_task(fctn(*args, **kwargs))
        else:
            fctn(*args, **kwargs)

    async def search_clans(
        self,
        *,
        name: str = None,
        war_frequency: str = None,
        location_id: int = None,
        min_members: int = None,
        max_members: int = None,
        min_clan_points: int = None,
        min_clan_level: int = None,
        label_ids: List[Union[Label, int]] = [],
        limit: int = None,
        before: str = None,
        after: str = None,
        cls: Type[Clan] = None,
        **kwargs,
    ) -> List[Clan]:
        """Search all clans by name and/or filtering the results using various criteria.

        At least one filtering criteria must be defined and if name is used as part
        of search, it is required to be at least three characters long.

        Parameters
        -----------
        name : str, optional
            The clan name.
        war_frequency : str, optional
            The war frequency.
        location_id : int, optional
            The location id.
        min_members : int, optional
            The minimum number of members.
        max_members : int, optional
            The maximum number of members.
        min_clan_points : int, optional
            The minumum clan points.
        min_clan_level : int, optional
            The minimum clan level.
        label_ids: :class:`List`[Union[:class:`coc.Label`, :class:`int`]]
            List of Labels or Label ids
        limit : int
            The number of clans to search for.
        cls:
            Target class to use to model that data returned

        Raises
        -------
        RuntimeError
            At least one filtering parameter must be passed.
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Clan`.
        Maintenance
            The API is currently in maintenance.
        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        List[:class:`Clan`]
            A list of all clans found matching criteria provided.

        """
        if not (
            name or war_frequency or location_id or min_members or max_members or min_clan_points or min_clan_level
        ):
            raise RuntimeError("At least one filtering parameter must be passed.")
        if cls is None:
            cls = self.objects_cls['Clan']
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        data = await self.http.search_clans(
            name=name,
            warFrequency=war_frequency,
            locationId=location_id,
            minMembers=min_members,
            maxMembers=max_members,
            minClanPoints=min_clan_points,
            minClanLevel=min_clan_level,
            label_ids=",".join([str(x.id) if isinstance(x, Label) else str(x) for x in label_ids
                                if isinstance(x, (Label, int,))]),
            limit=limit,
            before=before,
            after=after,
            **{**self._defaults, **kwargs}
        )
        return [cls(data=n, client=self, **kwargs) for n in data.get("items", [])]


    async def get_clan(self, tag: str, cls: Type[Clan] = None, **kwargs) -> Clan:
        """Get information about a single clan by clan tag.

        Clan tags can be found using clan search operation.

        Parameters
        -----------
        tag : str
            The clan tag to search for.

        cls:
            Target class to use to model that data returned

        Raises
        -------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Clan`.

        NotFound
            No clan was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`Clan`
            The clan with provided tag.
        """
        if cls is None:
            cls = self.objects_cls['Clan']
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        if self.correct_tags:
            tag = correct_tag(tag)

        data = await self.http.get_clan(tag,
                                        lookup_cache=kwargs.get("lookup_cache", self.lookup_cache),
                                        update_cache=kwargs.get("update_cache", self.update_cache),
                                        ignore_cached_errors=kwargs.get("ignore_cached_errors", self.ignore_cached_errors))
        return cls(data=data, client=self, **kwargs)

    def get_clans(self, tags: Iterable[str], cls: Type[Clan] = None, **kwargs) -> AsyncIterator[Clan]:
        """Get information about multiple clans by clan tag.
        Refer to `Client.get_clan` for more information.

        This returns a :class:`ClanIterator` which fetches the requested clan tags in parallel.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for clan in client.get_clans(tags):
                print(clan.name)

        Parameters
        -----------
        tags : Iterable[:class:`str`]
            An iterable of clan tags to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Clan`.


        Yields
        ------
        :class:`Clan`
            A clan matching one of the tags requested.
        """
        if cls is None:
            cls = self.objects_cls['Clan']
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        return ClanIterator(self, tags, cls, **{**self._defaults, **kwargs})


    async def get_members(self, clan_tag: str, *, limit: int = 0, after: str = "", before: str = "",
                          cls: Type[ClanMember] = None, **kwargs) -> List[ClanMember]:
        """List clan members.

        This is equivilant to ``(await Client.get_clan('tag')).members``.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.
        cls:
            Target class to use to model that data returned
        limit:
            class:`int`: Number of members to retrieve

        after:
            class:`str`: Pagination string to get page after

        before:
            class:`str`: Pagination string to get page before


        Raises
        -------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanMember`.

        NotFound
            No clan was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`ClanMember`]
            A list of members in the clan.
        """
        if cls is None:
            cls = self.objects_cls['ClanMember']
        if not issubclass(cls, ClanMember):
            raise TypeError("cls must be a subclass of ClanMember.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        args = {}
        if limit:
            args['limit'] = limit
        if after:
            args['after'] = after
        if before:
            args['before'] = before
        args['lookup_cache'] = kwargs.get("lookup_cache", self.lookup_cache)
        args['update_cache'] = kwargs.get("update_cache", self.update_cache)
        args['ignore_cached_errors'] = kwargs.get("ignore_cached_errors", self.ignore_cached_errors)

        data = await self.http.get_clan_members(clan_tag, **args)
        return [cls(data=mdata, client=self, **kwargs) for mdata in data.get("memberList", [])]

    async def get_war_log(
        self,
        clan_tag: str,
        cls: Type[ClanWarLogEntry] = None,
        page: bool = False,
        *,
        limit: int = 0,
        after: str = "",
        before: str = "",
        **kwargs
    ) -> ClanWarLog:
        """
        Retrieve a clan's clan war log. By default, this will return
        all the clan's log available in the API. This will of course consume
        memory. The option of limiting the amount of log items fetched
        can be controlled with the `limit` parameter. Additionally, if
        `paginate` is set to True, and an async for loop is performed
        on this object, then additional log items will be fetched but only
        consume the same amount of memory space at all time.


        .. note::

            Please see documentation for :class:`ClanWarLogEntry` for different attributes
            which are present when the entry is a regular clan war or a league clan war.
            The difference can be found with :attr:`ClanWarLogEntry.is_league_entry`.


        Parameters
        -----------
        clan_tag:
            class:`str`: The clan tag to search for.

        cls:
            Target class to use to model that data returned

        page:
            class:`bool`: Enable fetching logs while only holding the
            same amount of logs as `limit`. If `paginate` is set to True,
            and `limit` is set to default of 0, then `limit` will be set to
            10 automatically.

        limit:
            class:`int`: Number of logs to retrieve

        after:
            class:`str`: Pagination string to get page after

        before:
            class:`str`: Pagination string to get page before

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWarLogEntry`.

        NotFound
            No clan was found with the supplied tag.

        PrivateWarLog
            The clan's warlog is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`ClanWarLog`:
            Entries in the warlog of the requested clan.
        """
        if limit < 0:
            raise ValueError("Limit cannot be negative")
        if cls is None:
            cls = self.objects_cls['ClanWarLogEntry']
        if not issubclass(cls, ClanWarLogEntry):
            raise TypeError("cls must be a subclass of ClanWarLogEntry.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        # If paginate is enabled and limit is set to default of 0, then
        # set limit to a new default of 10
        if page:
            limit = limit if limit else 10
            
        

        try:
            return await ClanWarLog.init_cls(client=self,
                                             clan_tag=clan_tag,
                                             page=page,
                                             limit=limit,
                                             model=cls,
                                             after=after,
                                             before=before,
                                             **{**self._defaults, **kwargs})
        except Forbidden as exception:
            raise PrivateWarLog(exception.response,
                                exception.reason) from exception

    async def get_raid_log(
            self,
            clan_tag: str,
            cls: Type[RaidLogEntry] = None,
            page: bool = False,
            *,
            limit: int = 0,
            after: str = "",
            before: str = "",
            **kwargs
    ) -> RaidLog:
        """
        Retrieve a clan's Capital Raid Log. By default, this will return
        all the clan's log available in the API. This will of course consume
        memory. The option of limiting the amount of log items fetched
        can be controlled with the `limit` parameter. Additionally, if
        `paginate` is set to True, and an async for loop is performed
        on this object, then additional log items will be fetched but only
        consume the same amount of memory space at all time.


        Parameters
        -----------
        clan_tag:
            class:`str`: The clan tag to search for.

        cls:
            Target class to use to model that data returned

        page:
            class:`bool`: Enable fetching logs while only holding the
            same amount of logs as `limit`. If `paginate` is set to True,
            and `limit` is set to default of 0, then `limit` will be set to
            10 automatically.

        limit:
            class:`int`: Number of logs to retrieve

        after:
            class:`str`: Pagination string to get page after

        before:
            class:`str`: Pagination string to get page before

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RaidLogEntry`.

        NotFound
            No clan was found with the supplied tag.

        PrivateWarLog
            The clan's warlog is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`RaidLog`:
            Entries in the capital raid seasons of the requested clan.
        """

        if limit < 0:
            raise ValueError("Limit cannot be negative")
        if cls is None:
            cls = self.objects_cls['RaidLogEntry']
        if not issubclass(cls, RaidLogEntry):
            raise TypeError("cls must be a subclass of ClanWarLogEntry.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        # If paginate is enabled and limit is set to default of 0, then
        # set limit to a new default of 10
        if page:
            limit = limit if limit else 10

        try:
            return await RaidLog.init_cls(client=self,
                                          clan_tag=clan_tag,
                                          page=page,
                                          limit=limit,
                                          model=cls,
                                          after=after,
                                          before=before,
                                          **{**self._defaults, **kwargs}
                                          )
        except Forbidden as exception:
            raise PrivateWarLog(exception.response,
                                exception.reason) from exception

    async def get_clan_war(self, clan_tag: str, cls: Type[ClanWar] = None, **kwargs) -> ClanWar:
        """
        Retrieve information about clan's current clan war

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        NotFound
            No clan was found with the supplied tag.

        PrivateWarLog
            The clan's war log is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`ClanWar`
            The clan's current war.

        """
        if cls is None:
            cls = self.objects_cls['ClanWar']
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            data = await self.http.get_clan_current_war(clan_tag, **{**self._defaults, **kwargs})
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        return cls(data=data, client=self, clan_tag=clan_tag, **kwargs)

    def get_clan_wars(self, clan_tags: Iterable[str], cls: Type[ClanWar] = None, **kwargs) -> AsyncIterator[ClanWar]:
        """
        Retrieve information multiple clan's current clan wars

        This returns a :class:`coc.WarIterator` which fetches the requested wars in parallel.

        .. note ::

            This will skip any clans who have a private war-log.


        .. note ::

            This will not fetch any CWL wars. Use :meth:`Client.get_current_wars` for that.


        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for clan_war in Client.get_clan_wars(tags):
                print(clan_war.opponent)

        Parameters
        -----------
        clan_tags : Iterable[:class:`str`]
            An iterable of clan tags to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        NotFound
            No clan was found with the supplied tag.

        PrivateWarLog
            The clan's warlog is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Yields
        ------
        :class:`ClanWar`
            A war matching one of the tags requested.
        """
        if cls is None:
            cls = self.objects_cls['ClanWar']
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return ClanWarIterator(self, clan_tags, cls=cls, **{**self._defaults, **kwargs})

    async def get_league_group(
        self,
        clan_tag: str,
        cls: Type[ClanWarLeagueGroup] = None,
        **kwargs
    ) -> ClanWarLeagueGroup:
        """Retrieve information about clan's current clan war league group.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWarLeagueGroup`.

        NotFound
            No clan was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.
            This may be due to an API bug whereby requesting
            the league group of a clan searching for a CWL match will time out.


        Returns
        --------
        :class:`ClanWarLeagueGroup`
            The clan's war league group.
        """
        if cls is None:
            cls = self.objects_cls['ClanWarLeagueGroup']
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWarLeagueGroup):
            raise TypeError("cls must be a subclass of ClanWarLeagueGroup.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            data = await self.http.get_clan_war_league_group(clan_tag, **{**self._defaults, **kwargs})
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception
        except asyncio.TimeoutError:
            raise GatewayError(
                "Client timed out waiting for %s clan tag. This may be the result of an API bug which times out "
                "when requesting the league group of a clan searching for a Clan War League match."
            )

        return cls(data=data, client=self, **kwargs)

    async def get_league_war(self, war_tag: str, cls: Type[ClanWar] = None, **kwargs) -> ClanWar:
        """
        Retrieve information about a clan war league war.

        Parameters
        -----------
        war_tag : str
            The league war tag to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        NotFound
            No clan was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`ClanWar`
            The league war associated with the war tag
        """
        if cls is None:
            cls = self.objects_cls['ClanWar']
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of LeagueWar.")

        if self.correct_tags:
            war_tag = correct_tag(war_tag)

        try:
            data = await self.http.get_cwl_wars(war_tag, **{**self._defaults, **kwargs})
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        data["tag"] = war_tag  # API doesn't return this, even though it is in docs.
        return cls(data=data, client=self, **kwargs)

    def get_league_wars(
        self,
        war_tags: Iterable[str],
        clan_tag: str = None,
        cls: Type[ClanWar] = None,
        **kwargs
    ) -> AsyncIterator[ClanWar]:
        """
        Retrieve information about multiple league wars

        This returns a :class:`LeagueWarIterator` which fetches the requested clan tags in parallel.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for league_war in Client.get_league_wars(tags):
                print(league_war.opponent)

        Parameters
        -----------
        war_tags : Iterable[:class:`str`]
            An iterable of war tags to search for.
        clan_tag: :class:`str`
            An optional clan tag. If present, this will only return wars which belong to this clan.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        Yields
        ------
        :class:`ClanWar`
            A war matching one of the tags requested.
        """
        if cls is None:
            cls = self.objects_cls['ClanWar']
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return LeagueWarIterator(self, war_tags, clan_tag, cls, **{**self._defaults, **kwargs})

    async def get_current_war(
        self,
        clan_tag: str,
        cwl_round: WarRound = WarRound.current_war,
        cls: Type[ClanWar] = None,
        **kwargs
    ) -> Optional[ClanWar]:
        """Retrieve a clan's current war.

        Unlike ``Client.get_clan_war`` or ``Client.get_league_war``,
        this method will search for a regular war, and if the clan is in ``notInWar`` state,
        search for a current league war.

        This simplifies what would otherwise be 2-3 function calls to find a war.

        If you don't wish to search for CWL wars, use :meth:`Client.get_clan_war`.

        This method will consume the :exc:`PrivateWarLog` error, instead returning ``None``.

        .. note::

            You can differentiate between a regular clan war and a clan war league (CWL) war
            by using the helper property, :attr:`ClanWar.is_cwl`.


        Parameters
        -----------
        clan_tag : str
            An iterable of clan tag to search for.

        cwl_round: :class:`WarRound`
            An enum detailing the type of round to get. Could be ``coc.WarRound.previous_war``,
            ``coc.WarRound.current_war`` or ``coc.WarRound.preparation``.
            This defaults to ``coc.WarRound.current_war``.

        cls:
            Target class to use to model that data returned

        Raises
        -------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        NotFound
            No clan was found with the supplied tag.

        PrivateWarLog
            The clan's warlog is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`ClanWar`
            The clan's current war. Could be ``None``.

            If the clan is in CWL, the league group can be accessed via :attr:`ClanWar.league_group`.

            If you pass in a :class:`WarRound` and that round doesn't exist (yet), this will return ``None``.
        """
        kwargs = {**self._defaults, **kwargs}
        if cls is None:
            cls = self.objects_cls['ClanWar']
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            get_war = await self.get_clan_war(clan_tag, cls=cls, **kwargs)
        except PrivateWarLog:
            get_war = None

        if get_war and get_war.state != LEAGUE_WAR_STATE:
            return get_war

        try:
            league_group = await self.get_league_group(clan_tag, **kwargs)
        except (NotFound, GatewayError) as exception:
            # either they're not in cwl (NotFound)
            # or it's an API bug where league group endpoint will timeout when the clan is searching (GatewayError)
            if get_war is None:
                raise PrivateWarLog(exception.response, exception.reason) from exception
            return get_war

        if league_group.state == "notInWar" or league_group.state == "groupNotFound":
            return None
        last_round_active = league_group.number_of_rounds == len(league_group.rounds)
        if last_round_active and league_group.state != "ended":
            # there are the supposed number of rounds, but without any call we are unable to know if the last round is
            # currently in preparation or already in war
            async for war in self.get_league_wars(league_group.rounds[-1], cls=cls, **kwargs):
                if war.state == 'inWar':
                    # last round is already in war
                    last_round_active = True
                    break
                elif war.state == 'preparation':
                    # last round is still in preparation
                    last_round_active = False
                    break
        if cwl_round is WarRound.current_war and league_group.state == "preparation":
            return None  # for round 1 and 15min prep between rounds this is a shortcut.
        elif cwl_round is WarRound.current_preparation and league_group.state == "ended":
            return None  # for the end of CWL there's no next prep day.
        elif cwl_round is WarRound.current_war and len(league_group.rounds) < 2:
            round_tags = league_group.rounds[-1] # for the first round during prep already return round 1
        elif cwl_round is WarRound.current_war and (last_round_active or league_group.state == "ended"):
            round_tags = league_group.rounds[-1]  # for the end of CWL current_war should give the last war
        elif cwl_round is WarRound.previous_war and (last_round_active or league_group.state == "ended"):
            round_tags = league_group.rounds[-2]  # for the end of CWL previous_war should give the second last war
        elif cwl_round is WarRound.previous_war and len(league_group.rounds) < 3:
            return None  # no previous war for two rounds.
        elif cwl_round is WarRound.previous_war:
            round_tags = league_group.rounds[-3]
        elif cwl_round is WarRound.current_war:
            round_tags = league_group.rounds[-2]
        elif cwl_round is WarRound.current_preparation:
            round_tags = league_group.rounds[-1]
        else:
            return None

        kwargs["league_group"] = league_group
        kwargs["clan_tag"] = clan_tag
        async for war in self.get_league_wars(round_tags, cls=cls, **kwargs):
            if war.clan_tag == clan_tag:
                return war
            elif war.opponent.tag == clan_tag:
                tmp = war.clan
                war.clan = war.opponent
                war.opponent = tmp
                return war

    def get_current_wars(
        self,
        clan_tags: Iterable[str],
        cls: Type[ClanWar] = None,
        **kwargs
    ) -> AsyncIterator[ClanWar]:
        """Retrieve information multiple clan's current wars.

        See :meth:`Client.get_current_war` for more information.

        This returns a :class:`CurrentWarIterator` which fetches the requested clan tags in parallel.

        .. note ::

            This will skip any clans who have a private war-log.


        .. note ::

            This will fetch CWL wars, which may result in a slower operation due to multiple API calls.
            If you only wish to get regular wars, consider :meth:`Client.get_clan_wars`.


        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for war in Client.get_current_wars(tags):
                print(war.type)

        Parameters
        -----------
        clan_tags : Iterable[:class:`str`]
            An iterable of clan tags to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        Yields
        --------
        :class:`ClanWar`
            The clan war of a requested tag.
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if cls is None:
            cls = self.objects_cls.get("ClanWar")
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return CurrentWarIterator(client=self, tags=clan_tags, cls=cls, **{**self._defaults, **kwargs})

    async def search_locations(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[Location] = None,
                               **kwargs) -> List[Location]:
        """List all available locations

        Parameters
        -----------
        limit : int, optional
            Number of items to fetch. Default is None, which returns all available locations
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`Location`]
            The requested locations.
        """
        if cls is None:
            cls = self.objects_cls['Location']
        if not issubclass(cls, Location):
            raise TypeError("cls must be a subclass of Location.")
        data = await self.http.search_locations(limit=limit, before=before, after=after, **{**self._defaults, **kwargs})

        return [cls(data=n) for n in data["items"]]

    async def get_location(self, location_id: int, cls: Type[Location] = None, **kwargs) -> Location:
        """Get information about specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        NotFound
            No location was found with the supplied ID.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`Location`
            The requested location.
        """
        if cls is None:
            cls = self.objects_cls['Location']
        if not issubclass(cls, Location):
            raise TypeError("cls must be a subclass of Location.")
        data = await self.http.get_location(location_id, **{**self._defaults, **kwargs})
        return cls(data=data)

    async def get_location_named(self, location_name: str, cls: Type[Location] = None, **kwargs) -> Optional[Location]:
        """Get a location by name.

        This is equivalent to:

        .. code-block:: python3

            locations = await client.search_locations(limit=None)
            return utils.get(locations, name=location_name)


        Parameters
        -----------
        location_name : str
            The location name to search for
        cls:
            Target class to use to model that data returned

        Returns
        --------
        :class:`Location`
            The first location matching the location name.
        """
        if cls is None:
            cls = self.objects_cls['Location']
        if not issubclass(cls, Location):
            raise TypeError("cls must be a subclass of Location.")
        data = await self.http.search_locations(limit=None, before=None, after=None, **{**self._defaults, **kwargs})
        locations = [cls(data=n) for n in data["items"]]

        return get(locations, name=location_name)

    async def get_location_clans(
            self, location_id: int = "global", *, limit: int = None,
            before: str = None, after: str = None, cls: Type[RankedClan] = None,
            **kwargs
    ) -> List[RankedClan]:
        """Get clan rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for. Defaults to all locations (``global``).
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RankedClan`.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedClan`]
            The top clans for the requested location.
        """
        if cls is None:
            cls = self.objects_cls['RankedClan']
        if not issubclass(cls, RankedClan):
            raise TypeError("cls must be a subclass of RankedClan.")
        data = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after,
                                                  **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_location_clans_capital(
            self, location_id: int = "global", *, limit: int = None,
            before: str = None, after: str = None, cls: Type[RankedClan] = None,
            **kwargs
    ) -> List[RankedClan]:
        """Get clan capital rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for. Defaults to all locations (``global``).
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RankedClan`.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedClan`]
            The top clans for the requested location.
        """
        if cls is None:
            cls = self.objects_cls['RankedClan']
        if not issubclass(cls, RankedClan):
            raise TypeError("cls must be a subclass of RankedClan.")
        data = await self.http.get_location_clans_capital(location_id, limit=limit, before=before, after=after,
                                                          **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_location_players(
            self, location_id: int = "global", *, limit: int = None,
            before: str = None, after: str = None, cls: Type[RankedPlayer] = None,
            **kwargs
    ) -> List[RankedPlayer]:
        """Get player rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for. Defaults to all locations (global).
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RankedPlayer`.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            The top players for the requested location.
        """
        if cls is None:
            cls = self.objects_cls['RankedPlayer']
        if not issubclass(cls, RankedPlayer):
            raise TypeError("cls must be a subclass of RankedPlayer.")
        data = await self.http.get_location_players(location_id, limit=limit, before=before, after=after,
                                                    **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_location_clans_builder_base(
            self, location_id: int = "global", *, limit: int = None,
            before: str = None, after: str = None, cls: Type[RankedClan] = None, **kwargs
    ) -> List[RankedClan]:
        """Get clan builder base rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for. Defaults to all locations (global).
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RankedClan`.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedClan`]
            The top builder base-clans for the requested location.
        """
        if cls is None:
            cls = self.objects_cls['RankedClan']
        if not issubclass(cls, RankedClan):
            raise TypeError("cls must be a subclass of RankedClan.")
        data = await self.http.get_location_clans_builder_base(location_id, limit=limit, before=before, after=after,
                                                               **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_location_players_builder_base(
            self, location_id: int = "global", *, limit: int = None,
            before: str = None, after: str = None, cls: Type[RankedPlayer] = None, **kwargs
    ) -> List[RankedPlayer]:
        """Get player builder base rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for. Defaults to all locations (global).
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`RankedPlayer`.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            The top builder base players for the requested location.
        """
        if cls is None:
            cls = self.objects_cls['RankedPlayer']
        if not issubclass(cls, RankedPlayer):
            raise TypeError("cls must be a subclass of RankedPlayer.")
        data = await self.http.get_location_players_builder_base(location_id, limit=limit, before=before, after=after,
                                                                 **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    # leagues
    async def search_leagues(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[League] = None,
                             **kwargs) -> List[League]:
        """Get list of leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.


        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`League`]
            The requested leagues.
        """
        if cls is None:
            cls = self.objects_cls['League']
        if not issubclass(cls, League):
            raise TypeError("cls must be a subclass of League.")
        data = await self.http.search_leagues(limit=limit, before=before, after=after, **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_league(self, league_id: int, cls: Type[League] = None, **kwargs) -> League:
        """
        Get league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        NotFound
            No league was found with the supplied league ID.


        Returns
        --------
        :class:`League`
            The league with the requested ID
        """
        if cls is None:
            cls = self.objects_cls['League']
        if not issubclass(cls, League):
            raise TypeError("cls must be a subclass of League.")
        data = await self.http.get_league(league_id, **{**self._defaults, **kwargs})
        return cls(data=data, client=self)

    async def get_league_named(self, league_name: str, cls: Type[League] = None, **kwargs) -> Optional[League]:
        """Get a league by name.

        This is somewhat equivalent to

        .. code-block:: python3

            leagues = await client.search_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The league name to search for
        cls:
            Target class to use to model that data returned

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`League`
            The first league matching the league name. Could be ``None`` if not found.
        """
        if cls is None:
            cls = self.objects_cls['League']
        if not issubclass(cls, League):
            raise TypeError("cls must be a subclass of League.")
        return get(await self.search_leagues(cls=cls, **{**self._defaults, **kwargs}), name=league_name)

    async def search_builder_base_leagues(self, *, limit: int = None, before: str = None, after: str = None,
                                          cls: Type[BaseLeague] = None, **kwargs)-> List[BaseLeague]:
        """Get list of builder base leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned.


        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`BaseLeague`]
            The requested leagues.
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.search_builder_base_leagues(limit=limit, before=before, after=after,
                                                           **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_builder_base_league(self, league_id: int, cls: Type[BaseLeague] = None, **kwargs) -> BaseLeague:
        """
        Get builder base league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        NotFound
            No league was found with the supplied league ID.


        Returns
        --------
        :class:`BaseLeague`
            The league with the requested ID
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.get_builder_base_league(league_id, **{**self._defaults, **kwargs})
        return cls(data=data, client=self)

    async def get_builder_base_league_named(self, league_name: str, cls: Type[BaseLeague] = None, **kwargs) -> Optional[BaseLeague]:
        """Get a builder base league by name.

        This is somewhat equivalent to

        .. code-block:: python3

            leagues = await client.search_builder_base_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The builder base league name to search for
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`BaseLeague`
            The first league matching the league name. Could be ``None`` if not found.
        """
        return get(await self.search_builder_base_leagues(cls=cls, **{**self._defaults, **kwargs}), name=league_name)

    async def search_war_leagues(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[BaseLeague] = None,
                                 **kwargs) -> List[BaseLeague]:
        """Get list of war leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned.


        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`BaseLeague`]
            The requested leagues.
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.search_war_leagues(limit=limit, before=before, after=after, **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_war_league(self, league_id: int, cls: Type[BaseLeague] = None, **kwargs) -> BaseLeague:
        """
        Get war league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        NotFound
            No league was found with the supplied league ID.


        Returns
        --------
        :class:`BaseLeague`
            The league with the requested ID
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.get_war_league(league_id, **{**self._defaults, **kwargs})
        return cls(data=data, client=self)

    async def get_war_league_named(self, league_name: str, cls: Type[BaseLeague] = None, **kwargs) -> Optional[BaseLeague]:
        """Get a war league by name.

        This is somewhat equivalent to

        .. code-block:: python3

            leagues = await client.search_war_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The war league name to search for
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`BaseLeague`
            The first league matching the league name. Could be ``None`` if not found.
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        return get(await self.search_war_leagues(cls=cls, **{**self._defaults, **kwargs}), name=league_name)

    async def search_capital_leagues(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[BaseLeague] = None,
                                     **kwargs) -> List[BaseLeague]:
        """Get list of capital leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`BaseLeague`]
            The requested leagues.
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.search_capital_leagues(limit=limit, before=before, after=after,
                                                      **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_capital_league(self, league_id: int, cls: Type[BaseLeague] = None, **kwargs) -> BaseLeague:
        """
        Get capital league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        cls:
            Target class to use to model that data returned.
        
        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        NotFound
            No league was found with the supplied league ID.


        Returns
        --------
        :class:`BaseLeague`
            The league with the requested ID
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        data = await self.http.get_capital_league(league_id, **{**self._defaults, **kwargs})
        return cls(data=data, client=self)

    async def get_capital_league_named(self, league_name: str, cls: Type[BaseLeague] = None, **kwargs) -> Optional[BaseLeague]:
        """Get a capital league by name.

        This is somewhat equivalent to

        .. code-block:: python3

            leagues = await client.search_capital_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The capital league name to search for
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`BaseLeague`
            The first league matching the league name. Could be ``None`` if not found.
        """
        if cls is None:
            cls = self.objects_cls['BaseLeague']
        if not issubclass(cls, BaseLeague):
            raise TypeError("cls must be a subclass of BaseLeague.")
        return get(await self.search_capital_leagues(cls=cls, **{**self._defaults, **kwargs}), name=league_name)

    async def get_seasons(self, league_id: int = 29000022, **kwargs) -> List[str]:
        """Get league seasons.

        .. note::

            League season information is available only for Legend League, with a league ID 29000022.


        Parameters
        -----------
        league_id : str
            The League ID to search for. Defaults to the only league you can get season information for, legends.
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        InvalidArgument
            An invalid league_id was supplied. Currently, the only league supported is legends.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        -------
        List[str]
            The legend season IDs, in the form ``YYYY-MM``, ie. ``2020-04``.
        """
        data = await self.http.get_league_seasons(league_id, **{**self._defaults, **kwargs})
        return [entry["id"] for entry in data["items"]]

    async def get_season_rankings(self, league_id: int, season_id: str, cls: Type[RankedPlayer] = None, **kwargs) -> List[RankedPlayer]:
        """Get league season rankings.

        .. note::

            League season information is available only for Legend League, with a league ID 29000022.


        Parameters
        -----------
        league_id : str
            The League ID to search for.
        season_id : str
            The Season ID to search for.
        cls:
            Target class to use to model that data returned.
        
        Raises
        ------
        InvalidArgument
            An invalid league_id or season_id was supplied. Currently, the only league supported is legends.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            Top players for the requested season and league.
        """
        if cls is None:
            cls = self.objects_cls['RankedPlayer']
        if not issubclass(cls, RankedPlayer):
            raise TypeError("cls must be a subclass of RankedPlayer.")
        data = await self.http.get_league_season_info(league_id, season_id, **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data.get("items", [])]

    async def get_clan_labels(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[Label] = None, **kwargs
                              ) -> List[Label]:
        """Fetch all possible clan labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned.#
        
        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`Label`]
            A list of all possible clan labels.
        """
        if cls is None:
            cls = self.objects_cls['Label']
        if not issubclass(cls, Label):
            raise TypeError("cls must be a subclass of Label.")
        data = await self.http.get_clan_labels(limit=limit, before=before, after=after, **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    async def get_player_labels(self, *, limit: int = None, before: str = None, after: str = None, cls: Type[Label] = None, **kwargs
                                ) -> List[Label]:
        """Fetch all possible player labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.
        cls:
            Target class to use to model that data returned.
        
        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`Label`]
            A list of all possible player labels.
        """
        if cls is None:
            cls = self.objects_cls['Label']
        if not issubclass(cls, Label):
            raise TypeError("cls must be a subclass of Label.")
        data = await self.http.get_player_labels(limit=limit, before=before, after=after, **{**self._defaults, **kwargs})
        return [cls(data=n, client=self) for n in data["items"]]

    # players
    async def get_player(self, player_tag: str, cls: Type[Player] = Player,
                         load_game_data: bool = None, **kwargs) -> Player:
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to search for.

        cls:
            Target class to use to model that data returned

        Raises
        -------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Player`.

        NotFound
            No player was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`Player`
            The player with the tag.
        """
        if cls is None:
            cls = self.objects_cls['Player']
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        if self.correct_tags:
            player_tag = correct_tag(player_tag)

        data = await self.http.get_player(player_tag)
        return cls(data=data, client=self, load_game_data=load_game_data, **{**self._defaults, **kwargs})

    def get_players(self, player_tags: Iterable[str], cls: Type[Player] = None, load_game_data: bool = None, **kwargs) -> AsyncIterator[
        Player]:
        """Get information about a multiple players by player tag.
        Player tags can be found either in game or by from clan member lists.

        This returns a :class:`PlayerIterator` which fetches the requested player tags in parallel.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for player in Client.get_players(tags):
                print(player)

        Parameters
        ----------
        player_tags : Iterable[:class:`str`]
            An iterable of player tags to search for.

        cls:
            Target class to use to model that data returned

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Player`.

        Yields
        ------
        :class:`Player`
            A player matching one of the tags requested.
        """
        if cls is None:
            cls = self.objects_cls['Player']
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        return PlayerIterator(self, player_tags, cls=cls, load_game_data=load_game_data, **{**self._defaults, **kwargs} )

    async def verify_player_token(self, player_tag: str, token: str, **kwargs) -> bool:
        """Verify player API token that can be found from the game settings.

        This can be used to check that players own the game accounts they claim to own
        as they need to provide the one-time use API token that exists inside the game.

        Parameters
        ----------
        player_tag : str
            The player tag to verify.
        token : str
            The player's API token to verify.

        Raises
        ------
        NotFound
            No player was found with the supplied tag.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`bool`
            Whether the player tag and API token were a valid match.
        """
        if self.correct_tags:
            player_tag = correct_tag(player_tag)

        data = await self.http.verify_player_token(player_tag, token, lookup_cache=False, update_cache=False,
                                                   ignore_cached_errors=kwargs.get('ignore_cached_errors', self.ignore_cached_errors))
        return data and data["status"] == "ok" or False

    async def get_current_goldpass_season(self, cls: Type[GoldPassSeason] = None, **kwargs) -> GoldPassSeason:
        """Get the current gold pass season
        
        Parameters
        ----------
        cls:
            Target class to use to model that data returned.

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`GoldPassSeason`
            The gold pass season object of the current season"""
        if cls is None:
            cls = self.objects_cls['GoldPassSeason']
        if not issubclass(cls, GoldPassSeason):
            raise TypeError("cls must be a subclass of GoldPassSeason.")
        data = await self.http.get_current_goldpass_season(**{**self._defaults, **kwargs})
        return cls(data=data)

    def parse_army_link(self, link: str):
        """Transform an army link from in-game into a list of troops and spells.

        .. note::

            You must have Troop and Spell game metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        Example
        -------

        .. code-block:: python3

            troops, spells = client.parse_army_link("https://link.clashofclans.com/en?action=CopyArmy&army=u10x0-2x3s1x9-3x2")

            for troop, quantity in troops:
                print("The user wants {} {}s. They each have {} DPS.".format(quantity, troop.name, troops.dps))

            for spell, quantity in spells:
                print("The user wants {} {}s.".format(quantity, troop.name))


        Parameters
        ----------
        link: str
            The army share link, as copied from in-game.
            It should look something like: https://link.clashofclans.com/en?action=CopyArmy&army=u10x0-2x3s1x9-3x2

        Raises
        ------
        RuntimeError
            Troop and Spell game metadata must be loaded to use this feature.

        Returns
        --------
        List[Tuple[:class:`Troop`, :class:`int`]], List[Tuple[:class:`Spell`, :class:`int`]]
            A list of tuples containing the Troop or Spell object, and a quantity (1, 2, 3, 12 etc.)
            If none is found, this will still return 2 empty lists.
            If a troop isn't found, it will default to a Barbarian, as this is how the game parses the links.

        """
        if not (self._troop_holder.loaded and self._spell_holder.loaded):
            raise RuntimeError("Troop and Spell game metadata must be loaded to use this feature.")

        troops, spells = parse_army_link(link)

        lookup_troops = {t.id: t for t in self._troop_holder.items}
        lookup_spells = {s.id: s for s in self._spell_holder.items}

        return [(lookup_troops.get(t_id, self._troop_holder.get('Barbarian')), qty) for t_id, qty in troops], \
               [(lookup_spells.get(s_id, s_id), qty) for s_id, qty in spells]

    def create_army_link(self, **kwargs):
        r"""Transform troops and spells into an in-game army share link.

        .. note::

            You must have Troop and Spell game metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        Example
        -------

        .. code-block:: python3

            link = client.create_army_link(
                        barbarian=10,
                        archer=20,
                        hog_rider=30,
                        healing_spell=3,
                        poison_spell=2,
                        rage_spell=2
                    )
            print(link)  # prints https://link.clashofclans.com/en?action=CopyArmy&army=u0x10-1x20-11x30s1x3-9x2-2x2


        Parameters
        ----------
        \*\*kwargs
            Troop name to quantity mapping. See the example for more info.
            The troop name must match in-game **exactly**, and is case-insensitive.
            Replace spaces (" ") with an underscore.
            The quantity must be an integer.

        Raises
        ------
        RuntimeError
            Troop and Spell game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`str`
            The army share link.

        """

        base = "https://link.clashofclans.com/en?action=CopyArmy&army="

        if not (self._troop_holder.loaded and self._spell_holder.loaded):
            raise RuntimeError("Troop and Spell game metadata must be loaded to use this feature.")

        troops, spells = [], []
        for key, value in kwargs.items():
            if not isinstance(value, int):
                raise TypeError("Expected value to be of type integer.")

            key = key.replace("_", " ")

            troop = self._troop_holder.get(key)
            if troop:
                troops.append((troop, value))
            else:
                spell = self._spell_holder.get(key)
                if spell:
                    spells.append((spell, value))
                else:
                    raise ValueError("I couldn't find the troop or spell called '{}'.".format(key))

        if troops:
            base += "u" + "-".join("{qty}x{id}".format(qty=qty, id=troop.id - 4_000_000) for troop, qty in troops)
            
        if spells:
            base += "s" + "-".join("{qty}x{id}".format(qty=qty, id=spell.id - 26_000_000) for spell, qty in spells)

        return base

    def get_troop(
        self, name: str, is_home_village: bool = True, level: int = None, townhall: int = None
    ) -> Optional[Union[Type["Troop"], "Troop"]]:
        """Get an uninitiated Troop object with the given name.

        .. note::

            You must have Troop metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        .. note::

            Please see :ref:`game_data` for more info on how to use initiated vs uninitiated models.


        Example
        -------

        .. code-block:: python3

            troop = client.get_troop("Barbarian")

            for level, dps in enumerate(troop.dps, start=1):
                print(f"{troop.name} has {dps} DPS at Lv{level}")


        Parameters
        ----------
        name: str
            The troop name, which must match in-game **exactly**, but is case-insensitive.

        is_home_village: bool
            Whether the troop belongs to the home village or not. Defaults to True.

        level: Optional[int]
            The level to pass into the construction of the :class:`Troop` object. If this is present this will return an
            :ref:`initiated_objects`.

        townhall: Optional[int]
            The TH level to pass into the construction of the :class:`Troop` object. If this is ``None``,
            this will default to the TH level the ``level`` parameter is unlocked at.

        Raises
        ------
        RuntimeError
            Troop and Spell game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`Troop`
            If ``level`` is not ``None``, this will return an :ref:`initiated_objects`
            otherwise, this will return an :ref:`uninitiated_objects`

            If the troop is not found, this will return ``None``.

        """
        if not self._troop_holder.loaded:
            raise RuntimeError("Troop metadata must be loaded to use this feature.")

        troop = self._troop_holder.get(name, is_home_village)
        if troop is None:
            return None
        elif level is not None:
            data = {
                "name": troop.name,
                "level": level,
                "maxLevel": len(troop.lab_level) + 1,
                "village": "builderBase" if not troop._is_home_village else "home"
            }
            townhall = townhall or troop.lab_to_townhall[troop.lab_level[level]]
            return troop(data, townhall=townhall)
        else:
            return troop

    def get_spell(self, name: str, level: int = None, townhall: int = None) -> Optional[Union[Type["Spell"], "Spell"]]:
        """Get an uninitiated Spell object with the given name.

        .. note::

            You must have Spell metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        .. note::

            Please see :ref:`game_data` for more info on how to use initiated vs uninitiated models.


        Example
        -------

        .. code-block:: python3

            troop = client.get_spell("Healing Spell")

            for level, cost in enumerate(spell.upgrade_cost, start=1):
                print(f"{spell.name} has an upgrade cost of {cost} at Lv{level}")


        Parameters
        ----------
        name: str
            The troop name, which must match in-game **exactly**, but is case-insensitive.

        level: Optional[int]
            The level to pass into the construction of the :class:`Spell` object. If this is present this will return an
            :ref:`initiated_objects`. This can be ``None``, and you will get an uninitiated object.

        townhall: Optional[int]
            The TH level to pass into the construction of the :class:`Spell` object. If this is ``None``,
            this will default to the TH level the ``level`` parameter is unlocked at.


        Raises
        ------
        RuntimeError
            Troop and Spell game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`Spell`
            If ``level`` is not ``None``, this will return an :ref:`initiated_objects`
            otherwise, this will return an :ref:`uninitiated_objects`

            If the spell is not found, this will return ``None``.


        """
        if not self._spell_holder.loaded:
            raise RuntimeError("Spell metadata must be loaded to use this feature.")

        spell = self._spell_holder.get((name, True))
        if spell is None:
            return None
        elif level is not None:
            data = {
                "name": spell.name,
                "level": level,
                "maxLevel": len(spell.lab_level) + 1,
                "village": "home"
            }
            townhall = townhall or spell.lab_to_townhall[spell.lab_level[level]]
            return spell(data, townhall=townhall)
        else:
            return spell

    def get_hero(self, name: str, level: int = None, townhall: int = None) -> Optional[Union[Type["Hero"], "Hero"]]:
        """Get an uninitiated Hero object with the given name.

        .. note::

            You must have Hero metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        .. note::

            Please see :ref:`game_data` for more info on how to use initiated vs uninitiated models.


        Example
        -------

        .. code-block:: python3

            hero = client.get_hero("Archer Queen")

            for level, cost in enumerate(hero.upgrade_cost, start=1):
                print(f"{hero.name} has an upgrade cost of {cost} at Lv{level}")


        Parameters
        ----------
        name: str
            The hero name, which must match in-game **exactly**, but is case-insensitive.

        level: Optional[int]
            The level to pass into the construction of the :class:`Hero` object. If this is present this will return an
            :ref:`initiated_objects`.

        townhall: Optional[int]
            The TH level to pass into the construction of the :class:`Hero` object. If this is ``None``,
            this will default to the TH level the ``level`` parameter is unlocked at.


        Raises
        ------
        RuntimeError
            Hero game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`Hero`
            If ``level`` is not ``None``, this will return an :ref:`initiated_objects`
            otherwise, this will return an :ref:`uninitiated_objects`

            If the hero is not found, this will return ``None``.


        """
        if not self._hero_holder.loaded:
            raise RuntimeError("Hero metadata must be loaded to use this feature.")

        hero = self._hero_holder.get(name)
        if hero is None:
            return None
        elif level is not None:
            data = {
                "name": hero.name,
                "level": level,
                "maxLevel": len(hero.required_th_level) + 1,
                "village": "home"
            }
            townhall = townhall or hero.required_th_level[level]
            return hero(data, townhall=townhall)
        else:
            return hero

    def get_pet(self, name: str, level: int = None, townhall: int = None) -> Optional[Union[Type["Pet"], "Pet"]]:
        """Get an uninitiated Pet object with the given name.

        .. note::

            You must have Pet metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        .. note::

            Please see :ref:`game_data` for more info on how to use initiated vs uninitiated models.


        Example
        -------

        .. code-block:: python3

            pet = client.get_pet("Electro Owl")

            for level, cost in enumerate(pet.upgrade_cost, start=1):
                print(f"{pet.name} has an upgrade cost of {cost} at Lv{level}")


        Parameters
        ----------
        name: str
            The pet name, which must match in-game **exactly**, but is case-insensitive.

        level: Optional[int]
            The level to pass into the construction of the :class:`Pet` object. If this is present this will return an
            :ref:`initiated_objects`.

        townhall: Optional[int]
            The TH level to pass into the construction of the :class:`Pet` object. If this is ``None``,
            this will default to the TH level the ``level`` parameter is unlocked at.

        Raises
        ------
        RuntimeError
            Pet game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`Pet`
            If ``level`` is not ``None``, this will return an :ref:`initiated_objects`
            otherwise, this will return an :ref:`uninitiated_objects`

            If the pet is not found, this will return ``None``.


        """
        if not self._pet_holder.loaded:
            raise RuntimeError("Pet metadata must be loaded to use this feature.")

        pet = self._pet_holder.get(name)
        if pet is None:
            return None
        elif level is not None:
            data = {
                "name": pet.name,
                "level": level,
                "maxLevel": len(pet.required_th_level) + 1,
                "village": "home"
            }
            townhall = townhall or pet.required_th_level[level]
            return pet(data, townhall=townhall)
        else:
            return pet

    def get_equipment(self, name: str, level: int = None, townhall: int = None) -> Optional[Union[Type["Equipment"], "Equipment"]]:
        """Get an uninitiated Equipment object with the given name.

        .. note::

            You must have Equipment metadata loaded in order to use this method.
            This means ``load_game_metadata`` of ``Client`` must be **anything but** ``LoadGameData.never``.

        .. note::

            Please see :ref:`game_data` for more info on how to use initiated vs uninitiated models.


        Example
        -------

        .. code-block:: python3

            gear = client.get_equipment("Dark Orb")

            for level, cost in enumerate(gear.upgrade_cost, start=1):
                print(f"{gear.name} has an upgrade cost of {cost} at Lv{level}")


        Parameters
        ----------
        name: str
            The equipment name, which must match in-game **exactly**, but is case-insensitive.

        level: Optional[int]
            The level to pass into the construction of the :class:`Equipment` object. If this is present this will return an
            :ref:`initiated_objects`.

        townhall: Optional[int]
            The TH level to pass into the construction of the :class:`Equipment` object. If this is ``None``,
            this will default to the TH level the ``level`` parameter is unlocked at.

        Raises
        ------
        RuntimeError
            Pet game metadata must be loaded to use this feature.

        Returns
        --------
        :class:`Equipment`
            If ``level`` is not ``None``, this will return an :ref:`initiated_objects`
            otherwise, this will return an :ref:`uninitiated_objects`

            If the equipment is not found, this will return ``None``.


        """
        if not self._equipment_holder.is_loaded:
            raise RuntimeError("Equipment metadata must be loaded to use this feature.")

        equipment = self._equipment_holder.get(name)
        if equipment is None:
            return None
        elif level is not None:
            data = {
                "name": equipment.name,
                "level": level,
                "maxLevel": equipment.levels_available[-1],
                "village": "home"
            }
            #really hacky, need to find out why
            townhall = townhall or equipment.smithy_to_townhall[equipment._json_meta.get(str(level)).get("RequiredBlacksmithLevel")]
            return equipment(data, townhall=townhall)
        else:
            return equipment

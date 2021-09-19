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

from itertools import cycle
from pathlib import Path
from typing import AsyncIterator, Iterable, List, Optional, Type, Union, TYPE_CHECKING

import ujson

from .clans import Clan, RankedClan
from .errors import Forbidden, GatewayError, NotFound, PrivateWarLog
from .enums import WarRound
from .miscmodels import Label, League, Location, LoadGameData
from .hero import HeroHolder, PetHolder
from .http import HTTPClient, BasicThrottler, BatchThrottler
from .iterators import (
    PlayerIterator,
    ClanIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .players import Player, ClanMember, RankedPlayer
from .spell import SpellHolder
from .troop import TroopHolder
from .utils import correct_tag, get, parse_army_link
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup

if TYPE_CHECKING:
    from .hero import Hero, Pet
    from .spell import Spell
    from .troop import Troop


LOG = logging.getLogger(__name__)

LEAGUE_WAR_STATE = "notInWar"
KEY_MINIMUM, KEY_MAXIMUM = 1, 10

OBJECT_IDS_PATH = Path(__file__).parent.joinpath(Path("static/object_ids.json"))
ENGLISH_ALIAS_PATH = Path(__file__).parent.joinpath(Path("static/texts_EN.json"))
BUILDING_FILE_PATH = Path(__file__).parent.joinpath(Path("static/buildings.json"))


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
        The aiohttp connector to use. By default this is ``None``.

    timeout: :class:`float`
        The number of seconds before timing out with an API query. Defaults to 30.

    cache_max_size: :class:`int`
        The max size of the internal cache layer. Defaults to 10 000. Set this to ``None`` to remove any cache layer.

    load_game_data: :class:`LoadGameData`
        The option for how coc.py will load game data. See :ref:`initialising_game_data` for more info.


    Attributes
    ----------
    loop : :class:`asyncio.AbstractEventLoop`
        The loop that is used for HTTP requests
    """

    __slots__ = (
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
        "_ready",
        "correct_tags",
        "load_game_data",
        "_players",
        "_clans",
        "_wars",

        "_troop_holder",
        "_spell_holder",
        "_hero_holder",
        "_pet_holder",
    )

    def __init__(
        self,
        *,
        key_count: int = 1,
        key_names: str = "Created with coc.py Client",
        key_scopes: str = "clash",
        throttle_limit: int = 10,
        loop: asyncio.AbstractEventLoop = None,
        correct_tags: bool = True,
        throttler: Type[Union[BasicThrottler, BatchThrottler]] = BasicThrottler,
        connector=None,
        timeout: float = 30.0,
        cache_max_size: int = 10000,
        stats_max_size: int = 1000,
        load_game_data: LoadGameData = LoadGameData(default=True),
        **_,
    ):

        self.loop = loop or asyncio.get_event_loop()

        self.correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == self.correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(KEY_MINIMUM, KEY_MAXIMUM))

        self.key_names = key_names
        self.key_scopes = key_scopes
        self.throttle_limit = throttle_limit
        self.throttler = throttler
        self.connector = connector
        self.timeout = timeout
        self.cache_max_size = cache_max_size
        self.stats_max_size = stats_max_size

        self.http = None  # set in method login()
        self.correct_tags = correct_tags
        self.load_game_data = load_game_data

        # cache
        self._players = {}
        self._clans = {}
        self._wars = {}

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
        )

    def _load_holders(self):
        with open(OBJECT_IDS_PATH) as fp:
            object_ids = {v: k for k, v in ujson.load(fp).items()}

        with open(ENGLISH_ALIAS_PATH) as fp:
            english_aliases = ujson.load(fp)

        with open(BUILDING_FILE_PATH) as fp:
            buildings = ujson.load(fp)

        for supercell_name, data in buildings.items():
            if supercell_name == "Laboratory":
                lab_to_townhall = {index: th_level for index, th_level in enumerate(data["TownHallLevel"], start=1)}
                break
        else:
            # if the files failed to load, fallback to the old formula of lab level = TH level - 2
            lab_to_townhall = {i: i + 2 for i in range(1, 15)}

        for holder in (self._troop_holder, self._spell_holder, self._hero_holder, self._pet_holder):
            holder._load_json(object_ids, english_aliases, lab_to_townhall)

    def _create_holders(self):
        self._troop_holder, self._spell_holder, self._hero_holder, self._pet_holder = TroopHolder(), \
                                                                                      SpellHolder(), \
                                                                                      HeroHolder(), \
                                                                                      PetHolder()

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
        """Retrieves all keys and creates an HTTP connection ready for use.

        Parameters
        ----------
        keys
        """
        self.http = http = self._create_client(None, None)
        http._keys = keys
        http.keys = cycle(http._keys)
        http.key_count = len(keys)
        self.loop.run_until_complete(http.create_session(self.connector, self.timeout))
        self._create_holders()

        LOG.debug("HTTP connection created. Client is ready for use.")

    def close(self) -> None:
        """Closes the HTTP connection
        """
        LOG.info("Clash of Clans client logging out...")
        self.dispatch("on_client_close")
        self.loop.run_until_complete(self.http.close())
        self.loop.close()

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
        limit: int = None,
        before: str = None,
        after: str = None,
        cls: Type[Clan] = Clan,
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
        limit : int
            The number of clans to search for.

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
            limit=limit,
            before=before,
            after=after,
        )

        return [cls(data=n, client=self, **kwargs) for n in data.get("items", [])]

    async def get_clan(self, tag: str, cls: Type[Clan] = Clan, **kwargs) -> Clan:
        """Get information about a single clan by clan tag.

        Clan tags can be found using clan search operation.

        Parameters
        -----------
        tag : str
            The clan tag to search for.

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
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        if self.correct_tags:
            tag = correct_tag(tag)

        data = await self.http.get_clan(tag)
        return cls(data=data, client=self, **kwargs)

    def get_clans(self, tags: Iterable[str], cls: Type[Clan] = Clan, **kwargs) -> AsyncIterator[Clan]:
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

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Clan`.


        Yields
        ------
        :class:`Clan`
            A clan matching one of the tags requested.
        """
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        return ClanIterator(self, tags, cls, **kwargs)

    async def get_members(self, clan_tag: str, cls: Type[ClanMember] = ClanMember, **kwargs) -> List[ClanMember]:
        """List clan members.

        This is equivilant to ``(await Client.get_clan('tag')).members``.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

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
        if not issubclass(cls, ClanMember):
            raise TypeError("cls must be a subclass of ClanMember.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        data = await self.http.get_clan(clan_tag)
        return [cls(data=mdata, client=self, **kwargs) for mdata in data.get("memberList", [])]

    async def get_warlog(
        self,
        clan_tag: str,
        cls: Type[ClanWarLogEntry] = ClanWarLogEntry,
        **kwargs
    ) -> List[ClanWarLogEntry]:
        """Retrieve a clan's clan war log.

        .. note::

            Please see documentation for :class:`ClanWarLogEntry` for different attributes
            which are present when the entry is a regular clan war or a league clan war.
            The difference can be found with :attr:`ClanWarLogEntry.is_league_entry`.


        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

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
        List[:class:`ClanWarLogEntry`]
            Entries in the warlog of the requested clan.
        """
        if not issubclass(cls, ClanWarLogEntry):
            raise TypeError("cls must be a subclass of ClanWarLogEntry.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            data = await self.http.get_clan_warlog(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        return [cls(data=wdata, client=self, **kwargs) for wdata in data.get("items", [])]

    async def get_clan_war(self, clan_tag: str, cls: Type[ClanWar] = ClanWar, **kwargs) -> ClanWar:
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
            The clan's warlog is private.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        :class:`ClanWar`
            The clan's current war.

        """
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            data = await self.http.get_clan_current_war(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        return cls(data=data, client=self, clan_tag=clan_tag, **kwargs)

    def get_clan_wars(self, clan_tags: Iterable[str], cls: Type[ClanWar] = ClanWar, **kwargs) -> AsyncIterator[ClanWar]:
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
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return ClanWarIterator(self, clan_tags, cls=cls, **kwargs)

    async def get_league_group(
        self,
        clan_tag: str,
        cls: Type[ClanWarLeagueGroup] = ClanWarLeagueGroup,
        **kwargs
    ) -> ClanWarLeagueGroup:
        """Retrieve information about clan's current clan war league group.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

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
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWarLeagueGroup):
            raise TypeError("cls must be a subclass of ClanWarLeagueGroup.")

        if self.correct_tags:
            clan_tag = correct_tag(clan_tag)

        try:
            data = await self.http.get_clan_war_league_group(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception
        except asyncio.TimeoutError:
            raise GatewayError(
                "Client timed out waiting for %s clan tag. This may be the result of an API bug which times out "
                "when requesting the league group of a clan searching for a Clan War League match."
            )

        return cls(data=data, client=self, **kwargs)

    async def get_league_war(self, war_tag: str, cls: Type[ClanWar] = ClanWar, **kwargs) -> ClanWar:
        """
        Retrieve information about a clan war league war.

        Parameters
        -----------
        war_tag : str
            The league war tag to search for.

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
            The league war assosiated with the war tag
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of LeagueWar.")

        if self.correct_tags:
            war_tag = correct_tag(war_tag)

        try:
            data = await self.http.get_cwl_wars(war_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        data["tag"] = war_tag  # API doesn't return this, even though it is in docs.
        return cls(data=data, client=self, **kwargs)

    def get_league_wars(
        self,
        war_tags: Iterable[str],
        clan_tag: str = None,
        cls: Type[ClanWar] = ClanWar,
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

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`ClanWar`.

        Yields
        ------
        :class:`ClanWar`
            A war matching one of the tags requested.
        """
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return LeagueWarIterator(self, war_tags, clan_tag, cls, **kwargs)

    async def get_current_war(
        self,
        clan_tag: str,
        cwl_round: WarRound = WarRound.current_war,
        cls: Type[ClanWar] = ClanWar,
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
            league_group = await self.get_league_group(clan_tag)
        except (NotFound, GatewayError) as exception:
            # either they're not in cwl (NotFound)
            # or it's an API bug where league group endpoint will timeout when the clan is searching (GatewayError)
            if get_war is None:
                raise PrivateWarLog(exception.response, exception.reason) from exception
            return get_war

        is_prep = league_group.state == "preparation"

        if cwl_round is WarRound.current_war and league_group.state == "preparation":
            return None  # for round 1 and 15min prep between rounds this is a shortcut.
        elif cwl_round is WarRound.current_preparation and league_group.state == "warEnded":
            return None  # for the end of CWL there's no next prep day.
        elif cwl_round is WarRound.previous_war and len(league_group.rounds) == 1:
            return None  # no previous war for first rounds.
        elif cwl_round is WarRound.previous_war and is_prep:
            round_tags = league_group.rounds[-2]
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

    def get_current_wars(
        self,
        clan_tags: Iterable[str],
        cls: Type[ClanWar] = ClanWar,
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
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of either ClanWar.")

        return CurrentWarIterator(client=self, tags=clan_tags, cls=cls, **kwargs)

    # locations
    async def search_locations(self, *, limit: int = None, before: str = None, after: str = None) -> List[Location]:
        """List all available locations

        Parameters
        -----------
        limit : int, optional
            Number of items to fetch. Default is None, which returns all available locations
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
        List[:class:`Location`]
            The requested locations.
        """
        data = await self.http.search_locations(limit=limit, before=before, after=after)

        return [Location(data=n) for n in data["items"]]

    async def get_location(self, location_id: int) -> Location:
        """Get information about specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.

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
        data = await self.http.get_location(location_id)
        return Location(data=data)

    async def get_location_named(self, location_name: str) -> Optional[Location]:
        """Get a location by name.

        This is equivalent to:

        .. code-block:: python3

            locations = await client.search_locations(limit=None)
            return utils.get(locations, name=location_name)


        Parameters
        -----------
        location_name : str
            The location name to search for

        Returns
        --------
        :class:`Location`
            The first location matching the location name.
        """
        data = await self.http.search_locations(limit=None, before=None, after=None)
        locations = [Location(data=n) for n in data["items"]]

        return get(locations, name=location_name)

    async def get_location_clans(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
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

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedClan`]
            The top clans for the requested location.
        """

        data = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after)
        return [RankedClan(data=n, client=self) for n in data["items"]]

    async def get_location_players(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
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

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            The top players for the requested location.
        """
        data = await self.http.get_location_players(location_id, limit=limit, before=before, after=after)
        return [RankedPlayer(data=n, client=self) for n in data["items"]]

    async def get_location_clans_versus(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
    ) -> List[RankedClan]:
        """Get clan versus rankings for a specific location

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

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedClan`]
            The top versus-clans for the requested location.
        """
        data = await self.http.get_location_clans_versus(location_id, limit=limit, before=before, after=after)
        return [RankedClan(data=n, client=self) for n in data["items"]]

    async def get_location_players_versus(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
    ) -> List[RankedPlayer]:
        """Get player versus rankings for a specific location

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

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            The top versus players for the requested location.
        """
        data = await self.http.get_location_players_versus(location_id, limit=limit, before=before, after=after)
        return [RankedPlayer(data=n, client=self) for n in data["items"]]

    # leagues

    async def search_leagues(self, *, limit: int = None, before: str = None, after: str = None) -> List[League]:
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
        data = await self.http.search_leagues(limit=limit, before=before, after=after)
        return [League(data=n, client=self) for n in data["items"]]

    async def get_league(self, league_id: int) -> League:
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
        data = await self.http.get_league(league_id)
        return League(data=data, client=self)

    async def get_league_named(self, league_name: str) -> Optional[League]:
        """Get a location by name.

        This is somewhat equivilant to

        .. code-block:: python3

            leagues = await client.search_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The league name to search for

        Raises
        ------
        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        --------
        :class:`League`
            The first location matching the location name. Could be ``None`` if not found.
        """
        return get(await self.search_leagues(), name=league_name)

    async def get_seasons(self, league_id: int = 29000021) -> List[str]:
        """Get league seasons.

        .. note::

            League season information is available only for Legend League, with a league ID 29000021.


        Parameters
        -----------
        league_id : str
            The League ID to search for. Defaults to the only league you can get season information for, legends.

        Raises
        ------
        InvalidArgument
            An invalid league_id was supplied. Currently the only league supported is legends.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.

        Returns
        -------
        List[str]
            The legend season IDs, in the form ``YYYY-MM``, ie. ``2020-04``.
        """
        data = await self.http.get_league_seasons(league_id)
        return [entry["id"] for entry in data["items"]]

    async def get_season_rankings(self, league_id: int, season_id: int) -> List[RankedPlayer]:
        """Get league season rankings.

        .. note::

            League season information is available only for Legend League, with a league ID 29000021.


        Parameters
        -----------
        league_id : str
            The League ID to search for.
        season_id : str
            The Season ID to search for.

        Raises
        ------
        InvalidArgument
            An invalid league_id or season_id was supplied. Currently the only league supported is legends.

        Maintenance
            The API is currently in maintenance.

        GatewayError
            The API hit an unexpected gateway exception.


        Returns
        --------
        List[:class:`RankedPlayer`]
            Top players for the requested season and league.
        """
        data = await self.http.get_league_season_info(league_id, season_id)
        return [RankedPlayer(data=n, client=self) for n in data.get("items", [])]

    async def get_clan_labels(self, *, limit: int = None, before: str = None, after: str = None) -> List[Label]:
        """Fetch all possible clan labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
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
        List[:class:`Label`]
            A list of all possible clan labels.
        """
        data = await self.http.get_clan_labels(limit=limit, before=before, after=after)
        return [Label(data=n, client=self) for n in data["items"]]

    async def get_player_labels(self, *, limit: int = None, before: str = None, after: str = None) -> List[Label]:
        """Fetch all possible player labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
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
        List[:class:`Label`]
            A list of all possible player labels.
        """
        data = await self.http.get_player_labels(limit=limit, before=before, after=after)
        return [Label(data=n, client=self) for n in data["items"]]

    # players

    async def get_player(self, player_tag: str, cls: Type[Player] = Player, load_game_data: bool = None, **kwargs) -> Player:
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to search for.

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
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        if self.correct_tags:
            player_tag = correct_tag(player_tag)

        data = await self.http.get_player(player_tag)
        return cls(data=data, client=self, load_game_data=load_game_data, **kwargs)

    def get_players(self, player_tags: Iterable[str], cls: Type[Player] = Player, load_game_data: bool = None, **kwargs) -> AsyncIterator[Player]:
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

        Raises
        ------
        TypeError
            The ``cls`` parameter must be a subclass of :class:`Player`.

        Yields
        ------
        :class:`Player`
            A player matching one of the tags requested.
        """
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")
        if load_game_data and not isinstance(load_game_data, bool):
            raise TypeError("load_game_data must be either True or False.")

        return PlayerIterator(self, player_tags, cls=cls, load_game_data=load_game_data, **kwargs)

    async def verify_player_token(self, player_tag: str, token: str) -> bool:
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

        data = await self.http.verify_player_token(player_tag, token)
        return data and data["status"] == "ok" or False

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

        spell = self._spell_holder.get(name)
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

            troop = client.get_pet("Electro Owl")

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

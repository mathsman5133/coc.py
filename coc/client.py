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

from collections.abc import Iterable

from .clans import Clan, RankedClan
from .errors import Forbidden, GatewayError, NotFound, PrivateWarLog
from .enums import WarRound
from .miscmodels import Label, League, Location
from .http import HTTPClient, BasicThrottler
from .iterators import (
    PlayerIterator,
    ClanIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .players import Player, ClanMember, RankedPlayer
from .utils import get, corrected_tag
from .wars import ClanWar, ClanWarLogEntry, ClanWarLeagueGroup

LOG = logging.getLogger(__name__)

LEAGUE_WAR_STATE = "notInWar"
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


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
        "http",
        "_ready",
        "correct_tags",
        "_players",
        "_clans",
        "_wars",
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
        throttler=BasicThrottler,
        connector=None,
        timeout: float = 30.0,
        cache_max_size: int = 10000,
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

        self.http = None  # set in method login()
        self._ready = asyncio.Event(loop=loop)
        self.correct_tags = correct_tags

        # cache
        self._players = {}
        self._clans = {}
        self._wars = {}

    async def login(self, email: str, password: str):
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
        self.http = HTTPClient(
            client=self,
            email=email,
            password=password,
            key_names=self.key_names,
            key_scopes=self.key_scopes,
            loop=self.loop,
            key_count=self.correct_key_count,
            throttle_limit=self.throttle_limit,
            throttler=self.throttler,
            connector=self.connector,
            timeout=self.timeout,
            cache_max_size=self.cache_max_size,
        )
        await self.http.get_keys()
        await self._ready.wait()
        self._ready.clear()
        LOG.debug("HTTP connection created. Client is ready for use.")

    def close(self):
        """Closes the HTTP connection
        """
        LOG.info("Clash of Clans client logging out...")
        self.loop.run_until_complete(self.http.close())
        self.loop.close()
        self.dispatch("on_client_close")

    def dispatch(self, event_name: str, *args, **kwargs):
        """Dispatches an event listener matching the `event_name` parameter."""
        LOG.debug("Dispatching %s event", event_name)

        try:
            fctn = getattr(self, event_name)
        except AttributeError:
            return

        if asyncio.iscoroutinefunction(fctn):
            asyncio.ensure_future(fctn(*args, **kwargs), loop=self.loop)
        else:
            fctn(*args, **kwargs)

    async def reset_keys(self, number_of_keys: int = None):
        """Manually reset any number of keys.

        Under normal circumstances, this method should not need to be called.

        Parameters
        -----------
        number_of_keys : int
            The number of keys to reset. Defaults to None - all keys.
        """
        # pylint: disable=protected-access
        self._ready.clear()
        num = number_of_keys or len(self.http._keys)
        keys = self.http._keys
        for i in range(num):
            await self.http.reset_key(keys[i])
        self._ready.set()

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
        cls=Clan,
        **kwargs,
    ):
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

        Returns
        --------
        :class:`list` of :class:`SearchClan`
            A list of all clans found matching criteria provided.

        Raises
        -------
        HTTPException
            No options were passed.
        """
        if not (
            name or war_frequency or location_id or min_members or max_members or min_clan_points or min_clan_level
        ):
            raise TypeError("At least one filtering parameter must be passed.")
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

    @corrected_tag()
    async def get_clan(self, tag: str, cls=Clan, **kwargs):
        """Get information about a single clan by clan tag.

        Clan tags can be found using clan search operation.

        Parameters
        -----------
        tag : str
            The clan tag to search for.

        Returns
        --------
        :class:`SearchClan`
            The clan with provided tag.
        """
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        data = await self.http.get_clan(tag)
        clan = cls(data=data, client=self, **kwargs)

        # if self.UPDATE_CACHE:
        #     self._update_clan(clan)

        return clan

    def get_clans(self, tags: Iterable, cls=Clan, **kwargs):
        """Get information about multiple clans by clan tag.
        Refer to `Client.get_clan` for more information.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for clan in Client.get_clans(tags):
                print(clan.name)

        Parameters
        -----------
        tags : :class:`collections.Iterable`
            An iterable of clan tags to search for.


        Returns
        --------
        :class:`ClanIterator` of :class:`Clan`
            An iterable of the requested clans.
        """
        if not isinstance(tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if not issubclass(cls, Clan):
            raise TypeError("cls must be a subclass of Clan.")

        return ClanIterator(self, tags, cls, **kwargs)

    @corrected_tag(arg_name="clan_tag")
    async def get_members(self, clan_tag: str, cls=ClanMember, **kwargs):
        """List clan members.

        This is equivilant to ``(await Client.get_clan('tag')).members``.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        Returns
        --------
        List[:class:`ClanMember`]
            A list of :class:`ClanMember`s in the clan.
        """
        if not issubclass(cls, ClanMember):
            raise TypeError("cls must be a subclass of ClanMember.")

        data = await self.http.get_clan(clan_tag)
        return [cls(data=mdata, client=self, **kwargs) for mdata in data.get("memberList", [])]

    @corrected_tag(arg_name="clan_tag")
    async def get_warlog(self, clan_tag: str, cls=ClanWarLogEntry, **kwargs):
        """Retrieve a clan's clan war log.

        .. note::

            Please see documentation for :class:`ClanWarLogEntry` for different attributes
            which are present when the entry is a regular clan war or a league clan war.
            The difference can be found with :attr:`ClanWarLogEntry.is_league_entry`.


        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        Returns
        --------
        List[:class:`ClanWarLogEntry`]
            A list of the :class:`ClanWarLogEntry` in the warlog.

        Raises
        ------
        :exc:`PrivateWarLog`: The clan's warlog is private.
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWarLogEntry):
            raise TypeError("cls must be a subclass of ClanWarLogEntry.")

        try:
            data = await self.http.get_clan_warlog(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        return [cls(data=wdata, client=self, **kwargs) for wdata in data.get("items", [])]

    @corrected_tag(arg_name="clan_tag")
    async def get_clan_war(self, clan_tag: str, cls=ClanWar, **kwargs):
        """
        Retrieve information about clan's current clan war

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        Returns
        --------
        :class:`ClanWar`
            The clan's current war.

        Raises
        ------
        :exc:`PrivateWarLog`: The clan's war log is private.
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        try:
            data = await self.http.get_clan_current_war(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        return cls(data=data, client=self, clan_tag=clan_tag, **kwargs)

    def get_clan_wars(self, clan_tags: Iterable, cls=ClanWar, **kwargs):
        """
        Retrieve information multiple clan's current clan wars

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for clan_war in Client.get_clan_wars(tags):
                print(clan_war.opponent)

        Parameters
        -----------
        clan_tags : :class:`collections.Iterable`
            An iterable of clan tags to search for.

        Returns
        --------
        :class:`coc.iterators.WarIterator` of :class:`ClanWar`
            An iterator of all clan wars.
            This will skip clans who have a private war-log.
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return ClanWarIterator(self, clan_tags, cls=cls, **kwargs)

    @corrected_tag(arg_name="clan_tag")
    async def get_league_group(self, clan_tag: str, cls=ClanWarLeagueGroup, **kwargs):
        """Retrieve information about clan's current clan war league group.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.

        Returns
        --------
        :class:`ClanWarLeagueGroup`
            The clan's war league group.

        Raises
        ------
        :exc:`PrivateWarLog`: The clan's war log is private.
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWarLeagueGroup):
            raise TypeError("cls must be a subclass of ClanWarLeagueGroup.")

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

    @corrected_tag(arg_name="war_tag")
    async def get_league_war(self, war_tag: str, cls=ClanWar, **kwargs):
        """
        Retrieve information about a clan war league war.

        Parameters
        -----------
        war_tag : str
            The league war tag to search for.

        Returns
        --------
        :class:`ClanWar`
            The league war assosiated with the war tag
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of LeagueWar.")

        try:
            data = await self.http.get_cwl_wars(war_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception.reason) from exception

        data["tag"] = war_tag  # API doesn't return this, even though it is in docs.
        return cls(data=data, client=self, **kwargs)

    def get_league_wars(self, war_tags: Iterable, clan_tag: str = None, cls=ClanWar, **kwargs):
        """
        Retrieve information about multiple league wars

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for league_war in Client.get_league_wars(tags):
                print(league_war.opponent)

        Parameters
        -----------
        war_tags : :class:`collections.Iterable`
            An iterable of war tags to search for.
        clan_tag: Optional[:class:`str`]
            An optional clan tag. If present, this will only return wars which belong to this clan.

        Returns
        --------
        :class:`coc.iterators.LeagueWarIterator` of :class:`ClanWar`
            An iterator of wars.
        """
        if not isinstance(war_tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

        return LeagueWarIterator(self, war_tags, clan_tag, cls, **kwargs)

    @corrected_tag(arg_name="clan_tag")
    async def get_current_war(self, clan_tag: str, cwl_round=WarRound.current_war, cls=ClanWar, **kwargs):
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

        Returns
        --------
        :class:`ClanWar`
            The clan's current war.

            If no league group is found, or the group is in ``preparation``, this method will return the
            :class:`ClanWar`, which appears ``notInWar``, rather than returning ``None``.

            If the clan is in CWL, the league group can be accessed via :attr:`ClanWar.league_group`.
        """
        # pylint: disable=protected-access
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of ClanWar.")

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

    def get_current_wars(self, clan_tags: Iterable, cls=ClanWar, **kwargs):
        """Retrieve information multiple clan's current wars.

        See :meth:`Client.get_current_war` for more information.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for war in Client.get_current_wars(tags):
                print(war.type)

        Parameters
        -----------
        clan_tags : :class:`collections.Iterable`
            An iterable of clan tags to search for.

        Returns
        --------
        :class:`coc.iterators.CurrentWarIterator` of :class:`ClanWar`
            Current wars for the clans.
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if not issubclass(cls, ClanWar):
            raise TypeError("cls must be a subclass of either ClanWar.")

        return CurrentWarIterator(client=self, tags=clan_tags, cls=cls, **kwargs)

    # locations
    async def search_locations(self, *, limit: int = None, before: str = None, after: str = None):
        """List all available locations

        Parameters
        -----------
        limit : int, optional
            Number of items to fetch. Default is None, which returns all available locations
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.

        Returns
        --------
        :class:`list` of :class:`Location`
        """
        data = await self.http.search_locations(limit=limit, before=before, after=after)

        return [Location(data=n) for n in data["items"]]

    async def get_location(self, location_id: int):
        """Get information about specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.

        Returns
        --------
        :class:`Location`
        """
        data = await self.http.get_location(location_id)
        return Location(data=data)

    async def get_location_named(self, location_name: str):
        """Get a location by name.

        This is somewhat equivilant to:

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
    ):
        """Get clan rankings for a specific location

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


        Returns
        --------
        :class:`list` of :class:`Clan`
        """

        data = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after)
        return [RankedClan(data=n, client=self) for n in data["items"]]

    async def get_location_players(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
    ):
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

        Returns
        --------
        :class:`list` of :class:`Player`
        """
        data = await self.http.get_location_players(location_id, limit=limit, before=before, after=after)
        return [RankedPlayer(data=n, client=self) for n in data["items"]]

    async def get_location_clans_versus(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
    ):
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

        Returns
        --------
        :class:`list` of :class:`Clan`
        """
        data = await self.http.get_location_clans_versus(location_id, limit=limit, before=before, after=after)
        return [RankedClan(data=n, client=self) for n in data["items"]]

    async def get_location_players_versus(
        self, location_id: int = "global", *, limit: int = None, before: str = None, after: str = None
    ):
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

        Returns
        --------
        :class:`list` of :class:`Player`
        """
        data = await self.http.get_location_players_versus(location_id, limit=limit, before=before, after=after)
        return [RankedPlayer(data=n, client=self) for n in data["items"]]

    # leagues

    async def search_leagues(self, *, limit: int = None, before: str = None, after: str = None):
        """Get list of leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.

        Returns
        --------
        :class:`list` of :class:`League`
            Returns a list of all leagues found. Could be ``None``

        """
        data = await self.http.search_leagues(limit=limit, before=before, after=after)
        return [League(data=n, client=self) for n in data["items"]]

    async def get_league(self, league_id: int):
        """
        Get league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.

        Returns
        --------
        :class:`League`
        """
        data = await self.http.get_league(league_id)
        return League(data=data, client=self)

    async def get_league_named(self, league_name: str):
        """Get a location by name.

        This is somewhat equivilant to

        .. code-block:: python3

            leagues = await client.search_leagues(limit=None)
            return utils.get(leagues, name=league_name)


        Parameters
        -----------
        league_name : str
            The league name to search for

        Returns
        --------
        :class:`League`
            The first location matching the location name.
        """
        return get(await self.search_leagues(), name=league_name)

    async def get_seasons(self, league_id: int):
        """Get league seasons. Note that league season information is available only for Legend League.

        Parameters
        -----------
        league_id : str
            The League ID to search for.

        Returns
        --------
        :class:`dict`
            In the form

            .. code-block:: json

                {
                    "id": "string"
                }

            where ``id`` is the Season ID
        """
        data = await self.http.get_league_seasons(league_id)
        return data["items"]

    async def get_season_rankings(self, league_id: int, season_id: int):
        """Get league season rankings.
        Note that league season information is available only for Legend League.

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        season_id : str
            The Season ID to search for.

        Returns
        --------
        :class:`list` of :class:`RankedPlayer`
        """
        data = await self.http.get_league_season_info(league_id, season_id)
        return [RankedPlayer(data=n, client=self) for n in data.get("items", [])]

    async def get_clan_labels(self, *, limit: int = None, before: str = None, after: str = None):
        """List clan labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.

        Returns
        --------
        :class:`list` of :class:`Label`
        """
        data = await self.http.get_clan_labels(limit=limit, before=before, after=after)
        return [Label(data=n, client=self) for n in data["items"]]

    async def get_player_labels(self, *, limit: int = None, before: str = None, after: str = None):
        """List player labels.

        Parameters
        -----------
        limit : int
            The number of results to fetch.
        before : str, optional
            For use with paging. Not implemented yet.
        after: str, optional
            For use with paging. Not implemented yet.

        Returns
        --------
        :class:`list` of :class:`Label`
        """
        data = await self.http.get_player_labels(limit=limit, before=before, after=after)
        return [Label(data=n, client=self) for n in data["items"]]

    # players

    @corrected_tag(arg_name="player_tag")
    async def get_player(self, player_tag: str, cls=Player, **kwargs):
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to search for.

        Returns
        --------
        :class:`Player`
            The player with the tag.
        """
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")

        data = await self.http.get_player(player_tag)
        return cls(data=data, client=self, **kwargs)

    def get_players(self, player_tags: Iterable, cls=Player, **kwargs):
        """Get information about a multiple players by player tag.
        Player tags can be found either in game or by from clan member lists.

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for player in Client.get_players(tags):
                print(player)

        Parameters
        ----------
        player_tags : :class:`collections.Iterable`
            An iterable of player tags to search for.

        Returns
        --------
        :class:`PlayerIterator` of :class:`SearchPlayer`
        """
        if not isinstance(player_tags, Iterable):
            raise TypeError("Tags are not an iterable.")
        if not issubclass(cls, Player):
            raise TypeError("cls must be a subclass of Player.")

        return PlayerIterator(self, player_tags, cls=cls, **kwargs)

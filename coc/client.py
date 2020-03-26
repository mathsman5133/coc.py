# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2019 mathsman5133

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

from .cache import Cache, cached
from .clans import Clan, SearchClan
from .errors import Forbidden, NotFound, PrivateWarLog
from .miscmodels import Label, League, Location
from .http import HTTPClient
from .iterators import (
    PlayerIterator,
    ClanIterator,
    ClanWarIterator,
    LeagueWarIterator,
    CurrentWarIterator,
)
from .players import Player, LeagueRankedPlayer, SearchPlayer
from .utils import get, corrected_tag
from .wars import ClanWar, WarLog, LeagueWar, LeagueWarLogEntry, LeagueGroup

LOG = logging.getLogger(__name__)

LEAGUE_WAR_STATE = "notInWar"
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


class Client:
    """This is the client connection used to interact with the Clash of Clans API.

    Parameters
    -------------
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

    cache : :class:`Cache`, optional
        The :class:`Cache` used for interaction with the clients cache.
        If passed, this must inherit from :class:`Cache`. The default cache will be used if nothing is passed.

    correct_tags : :class:`bool`
        Whether the client should correct tags before requesting them from the API.
        This process involves stripping tags of whitespace and adding a `#` prefix if not present.
        Defaults to ``False``.

    Attributes
    -----------
    loop : :class:`asyncio.AbstractEventLoop`
        The loop that is used for HTTP requests
    """

    # pylint: disable=unused-argument
    # We do use them but through the `cache()` decorator.
    __slots__ = (
        "loop",
        "correct_key_count",
        "key_names",
        "throttle_limit",
        "http",
        "_ready",
        "cache",
        "correct_tags",
    )

    def __init__(
        self,
        *,
        key_count: int = 1,
        key_names: str = "Created with coc.py Client",
        throttle_limit: int = 10,
        loop: asyncio.AbstractEventLoop = None,
        cache=Cache,
        correct_tags: bool = False
    ):

        self.loop = loop or asyncio.get_event_loop()

        self.correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == self.correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(KEY_MINIMUM, KEY_MAXIMUM))

        self.key_names = key_names
        self.throttle_limit = throttle_limit

        self.http = None  # set in method login()
        self._ready = asyncio.Event(loop=loop)
        self.cache = cache
        self.correct_tags = correct_tags

    async def login(self, email: str, password: str):
        """Retrieves all keys and creates an HTTP connection ready for use.

        Parameters
        ------------
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
            loop=self.loop,
            key_count=self.correct_key_count,
            throttle_limit=self.throttle_limit,
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

    def create_cache(self):
        """Creates all cache instances and registers settings.

        This is called automatically in :meth:`coc.login()`
        """
        if not self.cache:
            return

        self.cache = self.cache(self)
        self.cache.register_cache_types()

    def dispatch(self, event_name: str, *args, **kwargs):
        """Dispatches an event listener matching the `event_name` parameter."""
        LOG.debug("Dispatching %s event", event_name)

        try:
            fctn = getattr(self, event_name)
        except AttributeError:
            return
        else:
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
        after: str = None
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

        clans = list(SearchClan(data=n, http=self.http) for n in data.get("items", []))

        return clans

    @corrected_tag()
    @cached("search_clans")
    async def get_clan(
        self, tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Get information about a single clan by clan tag.

        Clan tags can be found using clan search operation.

        Parameters
        -----------
        tag : str
            The clan tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`SearchClan`
            The clan with provided tag.
        """
        data = await self.http.get_clan(tag)
        return SearchClan(data=data, http=self.http)

    def get_clans(
        self, tags: Iterable, cache: bool = True, fetch: bool = True, update_cache: bool = True, **extra_options
    ):
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
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``
        **extra_options
            Extra options to use when passing in iterables other than normal lists.
            These kwargs could be any of the following:

            - index: bool - whether to index the values contained inside the iterable. Defaults to ``False``
            - index_type: Union[str, int] - the string or integer slice to index each value inside the iterable with.
            - attribute: str - the attribute to get for each item in the iterable. Defaults to ``None``.
            - index_before_attribute: bool - whether to index the item before getting an attribute (defaults to True)

            If none of these options are passed, the iterable passed in should be an instance of `collections.Iterable`.

        Returns
        --------
        :class:`ClanIterator` of :class:`SearchClan`
        """
        if not isinstance(tags, Iterable):
            raise TypeError("Tags are not an iterable.")

        return ClanIterator(self, tags, cache, fetch, update_cache, **extra_options)

    @corrected_tag(arg_name="clan_tag")
    async def get_members(
        self, clan_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """List clan members.

        This is equivilant to ``(await Client.get_clan('tag')).members``.

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`list` of :class:`BasicPlayer`
        """
        if cache:
            try:
                clan = await self.cache.get("search_clans", clan_tag)
            except KeyError:
                if fetch is False:
                    return
            else:
                if clan:
                    return clan.members

        data = await self.http.get_clan(clan_tag)
        clan = SearchClan(data=data, http=self.http)

        if update_cache and self.cache:
            await self.cache.set("search_clans", clan.tag, clan)

        return clan.members

    @corrected_tag(arg_name="clan_tag")
    @cached("war_logs")
    async def get_warlog(
        self, clan_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Retrieve clan's clan war log

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`list` of either :class:`WarLog` or :class:`LeagueWarLogEntry`
            Return type will depend on what kind of war it is.
            These two classes have different attributes.
        """
        # pylint: disable=protected-access
        try:
            data = await self.http.get_clan_warlog(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception._data)

        wars = []
        for war in data.get("items", []):
            # lately war log entries for sccwl can be distinguished by a `null` result
            if war.get("result") is None:
                wars.append(LeagueWarLogEntry(data=war, clan_tag=clan_tag, http=self.http))
                continue

            # for earlier logs this is distinguished by no opponent tag (result called `tie`)
            if war.get("opponent", {}).get("tag", None) is None:
                wars.append(LeagueWarLogEntry(data=war, clan_tag=clan_tag, http=self.http))
                continue

            wars.append(WarLog(data=war, clan_tag=clan_tag, http=self.http))

        if update_cache and self.cache:
            await self.cache.set("war_logs", wars[0].clan_tag, wars)

        return wars

    @corrected_tag(arg_name="clan_tag")
    @cached("clan_wars")
    async def get_clan_war(
        self, clan_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """
        Retrieve information about clan's current clan war

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`ClanWar`
        """
        # pylint: disable=protected-access
        try:
            data = await self.http.get_clan_current_war(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception._data)

        return ClanWar(data=data, clan_tag=clan_tag, http=self.http)

    def get_clan_wars(
        self, clan_tags: Iterable, cache: bool = True, fetch: bool = True, update_cache: bool = True, **extra_options
    ):
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
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``.
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``.
        **extra_options
            Extra options to use when passing in iterables other than normal lists.
            These kwargs could be any of the following:

            - index: bool - whether to index the values contained inside the iterable. Defaults to ``False``
            - index_type: Union[str, int] - the string or integer slice to index each value inside the iterable with.
            - attribute: str - the attribute to get for each item in the iterable. Defaults to ``None``.
            - index_before_attribute: bool - whether to index the item before getting an attribute (defaults to True)

            If none of these options are passed, the iterable passed in should be an instance of `collections.Iterable`.

        Returns
        --------
        :class:`coc.iterators.WarIterator` of :class:`ClanWar`
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError("Tags are not an iterable.")

        return ClanWarIterator(self, clan_tags, cache, fetch, update_cache, **extra_options)

    @corrected_tag(arg_name="clan_tag")
    @cached("league_groups")
    async def get_league_group(
        self, clan_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Retrieve information about clan's current clan war league group

        Parameters
        -----------
        clan_tag : str
            The clan tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``.
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``.

        Returns
        --------
        :class:`LeagueGroup`
        """
        # pylint: disable=protected-access
        try:
            data = await self.http.get_clan_war_league_group(clan_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception._data)

        return LeagueGroup(data=data, http=self.http)

    @corrected_tag(arg_name="war_tag")
    @cached("league_wars")
    async def get_league_war(
        self, war_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """
        Retrieve information about a clan war league war

        Parameters
        -----------
        war_tag : str
            The league war tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`LeagueWar`
        """
        # pylint: disable=protected-access
        try:
            data = await self.http.get_cwl_wars(war_tag)
        except Forbidden as exception:
            raise PrivateWarLog(exception.response, exception._data)

        return LeagueWar(data=data, http=self.http)

    def get_league_wars(
        self, war_tags: Iterable, cache: bool = True, fetch: bool = True, update_cache: bool = True, **extra_options
    ):
        """
        Retrieve information multiple clan's current league wars

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
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``.
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``.
        **extra_options
            Extra options to use when passing in iterables other than normal lists.
            These kwargs could be any of the following:

            - index: bool - whether to index the values contained inside the iterable. Defaults to ``False``
            - index_type: Union[str, int] - the string or integer slice to index each value inside the iterable with.
            - attribute: str - the attribute to get for each item in the iterable. Defaults to ``None``.
            - index_before_attribute: bool - whether to index the item before getting an attribute (defaults to True)

            If none of these options are passed, the iterable passed in should be an instance of `collections.Iterable`.

        Returns
        --------
        :class:`coc.iterators.LeagueWarIterator` of :class:`LeagueWar`
        """
        if not isinstance(war_tags, Iterable):
            raise TypeError("Tags are not an iterable.")

        return LeagueWarIterator(self, war_tags, cache, fetch, update_cache, **extra_options)

    @corrected_tag(arg_name="clan_tag")
    @cached("current_wars")
    async def get_current_war(
        self,
        clan_tag: str,
        *,
        league_war: bool = True,
        cache: bool = True,
        fetch: bool = True,
        update_cache: bool = True
    ):
        """Retrieve a clan's current war.

        Unlike ``Client.get_clan_war`` or ``Client.get_league_war``,
        this method will search for a regular war, and if the clan is in ``notInWar`` state,
        search for a current league war.

        This simplifies what would otherwise be 2-3 function calls to find a war.

        Parameters
        -----------
        clan_tag : str
            An iterable of clan tag to search for.
        league_war : bool
            Indicates whether the client should search for a league war.
            If this is ``False``, consider using ``Client.get_clan_war``.
            Defaults to ``True``.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``.
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``.

        Returns
        --------
        Either a :class:`ClanWar` or :class:`LeagueWar`, depending on the type of war in progress.
        These can be differentiated by through an ``isinstance(..)`` method,
        or by comparing ``type`` attributes.

        If no league group is found, or the group is in ``preparation``, this method will return the
        :class:`ClanWar`, which appears ``notInWar``, rather than returning ``None``.
        """
        get_war = await self.get_clan_war(clan_tag, cache=cache, fetch=fetch, update_cache=update_cache)
        if not get_war:
            return None
        if get_war.state != LEAGUE_WAR_STATE:
            return get_war
        if not league_war:
            return get_war

        try:
            league_group = await self.get_league_group(clan_tag, cache=cache, fetch=fetch, update_cache=update_cache)
        except NotFound:
            return get_war

        if league_group.state == "preparation":
            return get_war

        round_tags = league_group.rounds[-1]

        async for war in self.get_league_wars(round_tags, cache=cache, fetch=fetch, update_cache=update_cache):
            if war.clan_tag == clan_tag:
                return war

    def get_current_wars(
        self, clan_tags: Iterable, cache: bool = True, fetch: bool = True, update_cache: bool = True, **extra_options
    ):
        """Retrieve information multiple clan's current wars.

        These may be :class:`ClanWar` or :class:`LeagueWar`.

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
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``.
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``.
        **extra_options
            Extra options to use when passing in iterables other than normal lists.
            These kwargs could be any of the following:

            - index: bool - whether to index the values contained inside the iterable. Defaults to ``False``
            - index_type: Union[str, int] - the string or integer slice to index each value inside the iterable with.
            - attribute: str - the attribute to get for each item in the iterable. Defaults to ``None``.
            - index_before_attribute: bool - whether to index the item before getting an attribute (defaults to True)

            If none of these options are passed, the iterable passed in should be an instance of `collections.Iterable`.


        Returns
        --------
        :class:`coc.iterators.CurrentWarIterator` of either
        :class:`LeagueWar` or :class:`ClanWar`, or both.
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError("Tags are not an iterable.")

        return CurrentWarIterator(
            client=self, tags=clan_tags, cache=cache, fetch=fetch, update_cache=update_cache, **extra_options
        )

    # locations
    async def _populate_locations(self):
        if self.cache.get("locations", "fully_populated") is True:
            return await self.cache.get_limit("locations")

        await self.cache.clear("locations")
        all_locations = await self.search_locations(limit=None)

        for location in all_locations:
            await self.cache.set("locations", location.id, location)

        await self.cache.set("locations", "fully_populated", True)
        return all_locations

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
        if self.cache and await self.cache.get("locations", "fully_populated") is True:
            return await self.cache.get_limit("locations", limit)

        data = await self.http.search_locations(limit=limit, before=before, after=after)

        locations = list(Location(data=n) for n in data["items"])

        if self.cache:
            for location in locations:
                await self.cache.set("locations", location.id, location)

        return locations

    @cached("locations")
    async def get_location(
        self, location_id: int, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Get information about specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

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
            The first location matching the location name"""
        if self.cache:
            locations = await self._populate_locations()
        else:
            data = await self.http.search_locations(limit=None, before=None, after=None)
            locations = list(Location(data=n) for n in data["items"])

        return get(locations, name=location_name)

    async def get_location_clan(
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
        return list(Clan(data=n, http=self.http) for n in data["items"])

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
        return list(Player(data=n) for n in data["items"])

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
        return list(Clan(data=n, http=self.http) for n in data["items"])

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
        return list(Player(data=n) for n in data["items"])

    # leagues

    async def _populate_leagues(self):
        if await self.cache.get("leagues", "fully_populated") is True:
            return await self.cache.get_limit("leagues")

        await self.cache.clear("leagues")
        all_leagues = await self.search_leagues(limit=None)

        for league in all_leagues:
            await self.cache.set("leagues", league.id, league)

        await self.cache.set("leagues", "fully_populated", True)
        return all_leagues

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
        if self.cache and await self.cache.get("leagues", "fully_populated") is True:
            return await self.cache.get_limit("leagues", limit)

        data = await self.http.search_leagues(limit=limit, before=before, after=after)
        leagues = list(League(data=n, http=self.http) for n in data["items"])

        if self.cache:
            for league in leagues:
                await self.cache.set("leagues", league.id, league)

        return leagues

    @cached("leagues")
    async def get_league(
        self, league_id: int, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """
        Get league information

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`League`
        """
        data = await self.http.get_league(league_id)
        return League(data=data, http=self.http)

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
            The first location matching the location name"""
        if self.cache:
            leagues = await self._populate_leagues()
        else:
            data = await self.http.search_leagues(limit=None, before=None, after=None)
            leagues = list(League(data=n, http=self.http) for n in data["items"])

        return get(leagues, name=league_name)

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

    async def get_season_rankings(
        self, league_id: int, season_id: int, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Get league season rankings.
        Note that league season information is available only for Legend League.

        Parameters
        -----------
        league_id : str
            The League ID to search for.
        season_id : str
            The Season ID to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`list` of :class:`LeagueRankedPlayer`
        """
        # pylint: disable=too-many-arguments
        if cache and self.cache:
            try:
                data = await self.cache.get("seasons", "league_id")
                if data[season_id]:
                    return data

            except KeyError:
                pass

            if fetch is False:
                return None

        data = await self.http.get_league_season_info(league_id, season_id)
        players = list(LeagueRankedPlayer(data=n, http=self.http) for n in data.get("items", []))

        if self.cache and update_cache:
            await self.cache.set("seasons", "league_id", {season_id: players})

        return players

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
        return list(Label(data=n, http=self.http) for n in data["items"])

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
        return list(Label(data=n, http=self.http) for n in data["items"])

    # players

    @corrected_tag(arg_name="player_tag")
    @cached("search_players")
    async def get_player(
        self, player_tag: str, cache: bool = True, fetch: bool = True, update_cache: bool = True,
    ):
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to search for.
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``

        Returns
        --------
        :class:`SearchPlayer`
        """
        data = await self.http.get_player(player_tag)
        return SearchPlayer(data=data, http=self.http)

    def get_players(
        self, player_tags: Iterable, cache: bool = True, fetch: bool = True, update_cache: bool = True, **extra_options
    ):
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
        cache : bool
            Indicates whether to search the cache before making an HTTP request.
            Defaults to ``True``
        fetch : bool
            Indicates whether an HTTP call should be made if cache is empty.
            Defaults to ``True``. If this is ``False`` and item in cache was not found,
            ``None`` will be returned
        update_cache : bool
            Indicated whether the cache should be updated if an HTTP call is made.
            Defaults to ``True``
        **extra_options
            Extra options to use when passing in iterables other than normal lists.
            These kwargs could be any of the following:

            - index: bool - whether to index the values contained inside the iterable. Defaults to ``False``
            - index_type: Union[str, int] - the string or integer slice to index each value inside the iterable with.
            - attribute: str - the attribute to get for each item in the iterable. Defaults to ``None``.
            - index_before_attribute: bool - whether to index the item before getting an attribute (defaults to True)

            If none of these options are passed, the iterable passed in should be an instance of `collections.Iterable`.

        Returns
        --------
        :class:`PlayerIterator` of :class:`SearchPlayer`
        """
        if not isinstance(player_tags, Iterable):
            raise TypeError("Tags are not an iterable.")

        return PlayerIterator(self, player_tags, cache, fetch, update_cache, **extra_options)

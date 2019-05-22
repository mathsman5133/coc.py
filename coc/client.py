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
import traceback

from collections import Iterable
from itertools import chain

from .cache import Cache
from .clans import Clan, SearchClan
from .errors import ClashOfClansException, Forbidden, HTTPException
from .miscmodels import Location, League
from .http import HTTPClient
from .iterators import PlayerIterator, ClanIterator, WarIterator
from .nest_asyncio import apply
from .players import Player, LeagueRankedPlayer, SearchPlayer
from .utils import get
from .wars import CurrentWar, WarLog, LeagueWar, LeagueWarLogEntry, LeagueGroup

log = logging.getLogger(__name__)

LEAGUE_WAR_STATE = 'notInWar'
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


cache_search_clans = Cache()
cache_war_clans = Cache()

cache_search_players = Cache()
cache_war_players = Cache()

cache_current_wars = Cache()
cache_war_logs = Cache()

cache_league_groups = Cache()
cache_league_wars = Cache()

cache_locations = Cache()

cache_leagues = Cache()
cache_seasons = Cache()


def login(email, password, client=None, **kwargs):
    """Eases logging into the coc.py Client.

    This function makes logging into the client easy, returning the created client.

    Parameters
    -----------
    email : str
        Your password email from https://developer.clashofclans.com
        This is used when updating keys automatically if your IP changes
    password : str
        Your password login from https://developer.clashofclans.com
        This is used when updating keys automatically if your IP changes
    client
        The type of coc.py client to use. This could either be a
        :class:`Client` or :class:`EventsClient`, depending on which you wish
        to use.
    \*\*kwargs
        Any kwargs you wish to pass into the Client object.

    """
    if not client:
        client = Client

    c = client(**kwargs)
    c.loop.run_until_complete(c.login(email, password))
    return c


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

    Attributes
    -----------
    loop : :class:`asyncio.AbstractEventLoop`
        The loop that is used for HTTP requests
    """
    def __init__(self, *, key_count: int=1,
                 key_names: str='Created with coc.py Client',
                 throttle_limit: int=10,
                 loop: asyncio.AbstractEventLoop=None):

        self.loop = loop or asyncio.get_event_loop()
        self.correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == self.correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(
                KEY_MINIMUM, KEY_MAXIMUM))

        self.key_names = key_names
        self.throttle_limit = throttle_limit

        self.http = None  # set in method login()
        self._ready = asyncio.Event(loop=loop)

        log.info('Clash of Clans client created')

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
        self.http = HTTPClient(client=self, email=email, password=password,
                               key_names=self.key_names, loop=self.loop,
                               key_count=self.correct_key_count,
                               throttle_limit=self.throttle_limit)
        await self.http.get_keys()
        await self._ready.wait()
        self._ready.clear()
        log.debug('HTTP connection created. Client is ready for use.')

    def close(self):
        """
        Closes the HTTP connection
        """
        log.info('Clash of Clans client logging out...')
        self.loop.run_until_complete(self.http.close())
        self.loop.close()

    def event(self, fctn):
        """A decorator that registers an event.

        The only event at present is :func:`on_key_reset`.

        This could be a coro or regular function.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_key_reset(key):
                print('My new key is {}'.format(key))
        """
        setattr(self, fctn.__name__, fctn)
        log.info('Successfully registered %s event', fctn.__name__)
        return fctn

    def dispatch(self, event_name: str, *args, **kwargs):
        log.debug('Dispatching %s event', event_name)
        event = 'on_' + event_name

        try:
            fctn = getattr(self, event)
        except AttributeError:
            return
        else:
            if asyncio.iscoroutinefunction(fctn):
                asyncio.ensure_future(fctn(*args, **kwargs), loop=self.loop)
            else:
                fctn(*args, **kwargs)

    def get_cache(self, *cache_names):
        """Get a cache object by name.
        Cache objects are otherwise not accessible by the client except through this method.

        Parameters
        -----------
        cache_names : str
            The cache names to search for.

        Returns
        --------
        :class:`list` of cache objects found. If a name is not found, it will not be present in this list.
        """
        cache_objects = [self._get_cache_from_name(str(n)) for n in cache_names]
        return [n for n in cache_objects if n]

    def set_cache(self, *cache_to_edit, max_size: int=128, expiry: int=None):
        """Set the max size and expiry time for a cached object.

        .. note::

            Calling this method will override and create a new cache instance,
            removing all previously cached objects

        Parameters
        -----------
        cache_to_edit : str
            The name of cache type to change.
        max_size : int
            The max size of the created cache. Defaults to 128
        expiry : int, optional
            The expiry time in seconds of the cache.
            Defaults to None (cache does not expire)
        """
        for cache_type in cache_to_edit:
            attr = self._get_cache_from_name(str(cache_type))
            if not attr:
                raise ValueError('{} is not a valid cached data class type'.format(cache_to_edit))

            attr.clear(max_size, expiry)
            log.debug('Cache type %s has been set with max size %s and expiry %s seconds',
                      cache_type, max_size, expiry)

    @staticmethod
    def _get_cache_from_name(name):
        lookup = {
            'cache_search_clans': cache_search_clans,
            'cache_war_clans': cache_war_clans,

            'cache_search_players': cache_search_players,
            'cache_war_players': cache_war_players,

            'cache_current_wars': cache_current_wars,
            'cache_war_logs': cache_war_logs,

            'cache_league_groups': cache_league_groups,
            'cache_league_wars': cache_league_wars,

            'cache_locations': cache_locations,

            'cache_leagues': cache_leagues,
            'cache_seasons': cache_seasons
        }
        try:
            return lookup[str(name)]
        except KeyError:
            return None

    async def search_clans(self, *, name: str=None, war_frequency: str=None,
                           location_id: int = None, min_members: int=None, max_members: int=None,
                           min_clan_points: int = None, min_clan_level: int=None, limit: int=None,
                           before: int=None, after: int=None
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

        r = await self.http.search_clans(name=name, warFrequency=war_frequency, locationId=location_id,
                                         minMembers=min_members, maxMembers=max_members, minClanPoints=min_clan_points,
                                         minClanLevel=min_clan_level, limit=limit, before=before, after=after)

        clans = list(SearchClan(data=n, client=self) for n in r.get('items', []))

        return clans

    @cache_search_clans.get_cache()
    async def get_clan(self, tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
        """Get information about a single clan by clan tag. Clan tags can be found using clan search operation.

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
        r = await self.http.get_clan(tag)
        return SearchClan(data=r, client=self)

    def get_clans(self, tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
        """Get information about multiple clans by clan tag. Refer to `Client.get_clan` for more information.

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

        Returns
        --------
        :class:`ClanIterator` of :class:`SearchClan`
        """
        if not isinstance(tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return ClanIterator(self, tags, cache, fetch, update_cache)

    async def get_members(self, clan_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
            c = cache_search_clans.get(clan_tag)
            if c:
                return c.members

            if fetch is False:
                return None

        r = await self.http.get_clan(clan_tag)
        clan = SearchClan(data=r, client=self)

        if update_cache:
            cache_search_clans.add(clan.tag, clan)

        return clan.members

    @cache_war_logs.get_cache()
    async def get_warlog(self, clan_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_clan_warlog(clan_tag)

        wars = []
        for n in r.get('items', []):
            # lately war log entries for sccwl can be distinguished by a `null` result
            if n.get('result') is None:
                wars.append(LeagueWarLogEntry(data=n, clan_tag=clan_tag))
                continue

            # for earlier logs this is distinguished by no opponent tag (result called `tie`)
            if n.get('opponent', {}).get('tag', None) is None:
                wars.append(LeagueWarLogEntry(data=n, clan_tag=clan_tag))
                continue

            wars.append(WarLog(data=n, clan_tag=clan_tag, http=self.http))

        if update_cache:
            cache_war_logs.add(wars[0].clan.tag, wars)

        return wars

    @cache_current_wars.get_cache()
    async def get_current_war(self, clan_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        :class:`CurrentWar`
        """
        r = await self.http.get_clan_current_war(clan_tag)
        return CurrentWar(data=r, clan_tag=clan_tag, http=self.http)

    def get_current_wars(self, clan_tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
        """
        Retrieve information multiple clan's current clan wars

        Example
        ---------

        .. code-block:: python3

            tags = [...]
            async for clan_war in Client.get_current_wars(tags):
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

        Returns
        --------
        :class:`coc.iterators.WarIterator` of :class:`CurrentWar`
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return WarIterator(self, clan_tags, cache, fetch, update_cache)

    @cache_league_groups.get_cache()
    async def get_league_group(self, clan_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_clan_war_league_group(clan_tag)
        return LeagueGroup(data=r, http=self.http)

    @cache_league_wars.get_cache()
    async def get_league_war(self, war_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_cwl_wars(war_tag)
        return LeagueWar(data=r, http=self.http)

    # locations
    async def _populate_locations(self):
        if cache_locations.fully_populated is True:
            return cache_locations.get_all_values()

        cache_locations.clear()
        all_locations = await self.search_locations(limit=None)

        for n in all_locations:
            cache_locations.add(n.id, n)

        cache_locations.fully_populated = True
        return all_locations

    async def search_locations(self, *, limit: int=None,
                               before: int=None, after: int=None):
        """List all available locations

        Parameters
        -----------
        limit : int, optional
            Number of items to fetch. Default is None, which returns all available locations

        Returns
        --------
        :class:`list` of :class:`Location`
        """
        if cache_locations.fully_populated is True:
            return cache_locations.get_limit(limit)

        data = await self.http.search_locations(limit=limit, before=before, after=after)

        locations = list(Location(data=n) for n in data['items'])

        for n in locations:
            cache_locations.add(n.id, n)

        return locations

    @cache_locations.get_cache()
    async def get_location(self, location_id: int, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_location(location_id)
        return Location(data=r)

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
        locations = await self._populate_locations()
        return get(locations, name=location_name)

    async def get_location_clan(self, location_id: int, *, limit: int=None,
                                before: int=None, after: int=None):
        """Get clan rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        limit : int
            The number of results to fetch.

        Returns
        --------
        :class:`list` of :class:`Clan`
        """

        r = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after)
        return list(Clan(data=n, http=self.http) for n in r['items'])

    async def get_location_players(self, location_id: int, *, limit: int=None,
                                   before: int=None, after: int=None):
        """Get player rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        limit : int
            The number of results to fetch.

        Returns
        --------
        :class:`list` of :class:`Player`
        """
        r = await self.http.get_location_players(location_id, limit=limit, before=before, after=after)
        return list(Player(data=n) for n in r['items'])

    async def get_location_clans_versus(self, location_id: int, *, limit: int=None,
                                        before: int=None, after: int=None):
        """Get clan versus rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        limit : int
            The number of results to fetch.

        Returns
        --------
        :class:`list` of :class:`Clan`
        """
        r = await self.http.get_location_clans_versus(location_id, limit=limit, before=before, after=after)
        return list(Clan(data=n, http=self.http) for n in r['items'])

    async def get_location_players_versus(self, location_id: int, *, limit: int = None,
                                          before: int = None, after: int = None):
        """Get player versus rankings for a specific location

        Parameters
        -----------
        location_id : int
            The Location ID to search for.
        limit : int
            The number of results to fetch.

        Returns
        --------
        :class:`list` of :class:`Player`
        """
        r = await self.http.get_location_players_versus(location_id, limit=limit, before=before, after=after)
        return list(Player(data=n) for n in r['items'])

    # leagues

    async def _populate_leagues(self):
        if cache_leagues.fully_populated is True:
            return cache_leagues.get_all_values()

        cache_leagues.clear()
        all_leagues = await self.search_leagues(limit=None)

        for n in all_leagues:
            cache_leagues.add(n.id, n)

        cache_leagues.fully_populated = True
        return all_leagues

    async def search_leagues(self, *, limit: int=None, before: int=None, after: int=None):
        """Get list of leagues.

        Parameters
        -----------
        limit : int
            Number of items to fetch. Defaults to ``None`` (all leagues).

        Returns
        --------
        :class:`list` of :class:`League`
            Returns a list of all leagues found. Could be ``None``

        """
        if cache_leagues.fully_populated is True:
            return cache_leagues.get_limit(limit)

        r = await self.http.search_leagues(limit=limit, before=before, after=after)
        leagues = list(League(data=n) for n in r['items'])

        for n in leagues:
            cache_leagues.add(n.id, n)

        return leagues

    @cache_leagues.get_cache()
    async def get_league(self, league_id: int, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_league(league_id)
        return League(data=r)

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
        leagues = await self._populate_leagues()
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
        r = await self.http.get_league_seasons(league_id)
        return r['items']

    async def get_season_rankings(self, league_id: int, season_id: int, cache: bool=False,
                                  fetch: bool=True, update_cache: bool=True):
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
        if cache:
            try:
                data = cache_seasons.get(league_id)[season_id]
                if data:
                    return data

            except KeyError:
                pass

            if fetch is False:
                return None

        r = await self.http.get_league_season_info(league_id, season_id)
        players = list(LeagueRankedPlayer(data=n, http=self.http) for n in r.get('items', []))

        if update_cache:
            cache_seasons.add(league_id, {season_id: players})

        return players

    # players

    @cache_search_players.get_cache()
    async def get_player(self, player_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_player(player_tag)
        return SearchPlayer(data=r, http=self.http)

    def get_players(self, player_tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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

        Returns
        --------
        :class:`PlayerIterator` of :class:`SearchPlayer`
        """
        if not isinstance(player_tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return PlayerIterator(self, player_tags, cache, fetch, update_cache)


class EventsClient(Client):
    def __init__(self, **options):
        """The client connection used to interact with the API and manage events.

        This client provides all functionality of :class:`Client`, with an additional
        events side.

        Events will look for changes in tags supplied by the user, dispatching 'events'
        when a change is found. Events are created and registered by the user, and
        the client will automatically dispatch events to these functions, when events
        have been enabled.

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

        Attributes
        -----------
        loop : :class:`asyncio.AbstractEventLoop`
            The loop that is used for HTTP requests
        """
        super().__init__(**options)
        apply(self.loop)
        self._setup()

    def _setup(self):
        self._clan_updates = None
        self._player_updates = None
        self._war_updates = None

        self._active_state_tasks = {}

        self._clan_retry_interval = 600
        self._player_retry_interval = 600
        self._war_retry_interval = 600

        self._clan_update_event = asyncio.Event(loop=self.loop)
        self._war_update_event = asyncio.Event(loop=self.loop)
        self._player_update_event = asyncio.Event(loop=self.loop)

        self._updater_tasks = {}

        self.extra_events = {}

        self._updater_tasks['clan'] = self.loop.create_task(self._clan_updater())
        self._updater_tasks['war'] = self.loop.create_task(self._war_updater())
        self._updater_tasks['player'] = self.loop.create_task(self._player_updater())

    def close(self):
        """Closes the client and all running tasks.
        """
        tasks = {t for t in asyncio.Task.all_tasks(loop=self.loop) if not t.done()}
        if not tasks:
            return
        for t in tasks:
            t.cancel()
        self.loop.run_until_complete(self.http.close())
        self.loop.close()

    def dispatch(self, event_name: str, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            asyncio.ensure_future(self._run_event(ev, event, *args, **kwargs), loop=self.loop)

    def event(self, fctn, name=None):
        """A decorator or regular function that registers an event.

        The function **must** be a coroutine.

        Parameters
        ------------
        fctn : function
            The function to be registered (not needed if used with a decorator)
        name : str
            The name of the function to be registered. Defaults to the function name.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_player_update(old_player, new_player):
                print('{} has updated their profile!'.format(old_player))

        Returns
        --------
        function : The function registered
        """
        if not asyncio.iscoroutinefunction(fctn):
            raise TypeError('event {} must be a coroutine function'.format(fctn.__name__))

        name = name or fctn.__name__

        if name in self.extra_events:
            self.extra_events[name].append(fctn)
        else:
            self.extra_events[name] = [fctn]

        return fctn

    def add_events(self, *fctns, function_dicts: dict=None):
        """Provides an alternative method to adding events.

        You can either provide functions as named args or as a dict of {function: name...} values.

        Example
        --------

        .. code-block:: python3

            client.add_events(on_member_update, on_clan_update, on_war_attack)
            # or, using a dict:
            client.add_events(function_dicts={on_update: 'on_member_update', on_update_2: 'on_clan_update'})

        Parameters
        -----------
        fctns : function
            Named args of functions to register. The name of event is dictated by function name.
        function_dicts : dict
            Dictionary of ``{function: 'event_name'}`` values.
        """
        for f in fctns:
            self.event(f)
        if function_dicts:
            for f, n in function_dicts.items():
                self.event(f, name=n)

    def run_forever(self):
        """A blocking call which runs the loop and script.

        This is useful if you have no other clients to deal
        with and just wish to run the script and receive updates indefinately.

        Roughly equivilant to:

        ..code-block:: python3

            try:
                client.loop.run_forever()
            except KeyboardInterrupt:
                client.close()
            finally:
                client.loop.close()

        """
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            log.info('Terminating bot and event loop.')
            self.close()

    async def _run_event(self, event_name, coro, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_event_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    async def on_event_error(self, event_name, *args, **kwargs):
        """Event called when an event fails.

        By default this will print the traceback
        This can be overridden by either using @client.event or through subclassing EventsClient.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_event_error(event_name, *args, **kwargs):
                print('Ignoring exception in {}'.format(event_name))

            class Client(events.EventClient):
                async def on_event_error(event_name, *args, **kwargs):
                    print('Ignoring exception in {}'.format(event_name))

        """
        print('Ignoring exception in {}'.format(event_name))
        traceback.print_exc()

    async def add_clan_update(self, tags: Iterable, *, member_updates=False, retry_interval=600):
        """Subscribe clan tags to events.

        Parameters
        ------------
        tags : :class:`collections.Iterable`
            The clan tags to add.
        member_updates : bool
            Whether to subscribe to events regarding players in that clan. Defaults to ``False``
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        if not self._clan_updates:
            self._clan_updates = tags
        else:
            self._clan_updates = chain(self._clan_updates, tags)

        if member_updates:
            async for clan in self.get_clans(tags):
                await self.add_player_update((n.tag for n in clan._members), retry_interval=retry_interval)
            self._player_retry_interval = retry_interval

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._clan_retry_interval = retry_interval

    def add_war_update(self, tags: Iterable, *, retry_interval=600):
        """Subscribe clan tags to war events.

        Parameters
        ------------
        tags : :class:`collections.Iterable`
            The clan tags to add.
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        if not self._war_updates:
            self._war_updates = tags
        else:
            self._war_updates = chain(self._war_updates, tags)

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._war_retry_interval = retry_interval

    def add_player_update(self, tags: Iterable, retry_interval=600):
        """Subscribe player tags to player update events.

        Parameters
        ------------
        tags : :class:`collections.Iterable`
            The player tags to add.
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        if not self._player_updates:
            self._player_updates = tags
        else:
            self._player_updates = chain(self._player_updates, tags)

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._player_retry_interval = retry_interval

    def start_updates(self, event_name='all'):
        """Starts an, or all, events.

        .. note::
            This method **must** be called before any events are run.

        The lookup for event_name is as follows:
        'clan' - to register clan events
        'player' - to register player events
        'war' - to register war events
        'all' - to register all of the above.

        Parameters
        -----------
        event_name : str
            See above for which string corresponds to events.
            Defaults to 'all'
        """
        lookup = {
            'clan': self._clan_update_event,
            'player': self._player_update_event,
            'war': self._war_update_event
        }
        if event_name == 'all':
            events = lookup.values()
        else:
            events = [lookup[event_name]]

        for e in events:
            e.set()

    def stop_updates(self, event_name='all'):
        """Stops an, or all, events.

        .. note::
            This method **must** be called in order to stop any events.

        The lookup for event_name is as follows:
        'clan' - to stop clan events
        'player' - to stop player events
        'war' - to stop war events
        'all' - to stop all of the above.

        Parameters
        -----------
        event_name : str
            See above for which string corresponds to events.
            Defaults to 'all'
        """

        lookup = {
            'clan': self._clan_update_event,
            'player': self._player_update_event,
            'war': self._war_update_event
        }
        if event_name == 'all':
            events = lookup.values()
        else:
            events = [lookup[event_name]]

        for e in events:
            e.clear()

    async def _war_updater(self):
        try:
            while self.loop.is_running():
                await self._war_update_event.wait()
                await self._update_wars()
                await asyncio.sleep(self._war_retry_interval)
        except (
                OSError,
                asyncio.CancelledError,
                HTTPException,
                ClashOfClansException
        ):

            await self.on_event_error('on_war_update')
            return await self._war_updater()

    async def _clan_updater(self):
        try:
            while self.loop.is_running():
                await self._clan_update_event.wait()
                await self._update_clans()
                await asyncio.sleep(self._player_retry_interval)
        except (
                OSError,
                asyncio.CancelledError,
                HTTPException,
                ClashOfClansException
        ):
            await self.on_event_error('on_clan_update')
            return await self._clan_updater()

    async def _player_updater(self):
        try:
            while self.loop.is_running():
                await self._player_update_event.wait()
                await self._update_players()
                await asyncio.sleep(self._clan_retry_interval)
        except (
                OSError,
                asyncio.CancelledError,
                HTTPException,
                ClashOfClansException
        ):
            await self.on_event_error('on_player_update')
            return await self._player_updater()

    async def _check_member_count(self, cached_clan, new_clan):
        differences = [n for n in new_clan._members if n not in set(n.tag for n in cached_clan._members)]

        for tag in differences:
            new_member = get(new_clan._members, tag=tag)
            if new_member:
                self.dispatch('clan_member_join', new_member, new_clan)
                continue

            member_left = get(cached_clan._members, tag=tag)
            if member_left:
                self.dispatch('clan_member_leave', member_left, new_clan)
                continue

        return

    async def _update_clans(self):
        if not self._clan_updates:
            return

        async for clan in self.get_clans(self._clan_updates, update_cache=False):
            cached_clan = cache_search_clans.get(clan.tag)
            if not cached_clan:
                cache_search_clans.add(clan.tag, clan)
                continue

            if clan == cached_clan:
                continue

            self.dispatch('clan_update', cached_clan, clan)

            if clan.member_count != cached_clan:
                await self._check_member_count(cached_clan, clan)
                cached_clan._data['memberCount'] = clan.member_count  # hack for next line

            if clan._data == cached_clan._data:
                cache_search_clans.add(clan.tag, clan)
                continue

            self.dispatch('clan_settings_update', cached_clan, clan)
            cache_search_clans.add(clan.tag, clan)

    async def _wait_for_state_change(self, state_to_wait_for, war):
        if state_to_wait_for == 'inWar':
            to_sleep = war.start_time.seconds_until
        elif state_to_wait_for == 'warEnded':
            to_sleep = war.end_time.seconds_until
        else:
            return

        await asyncio.sleep(to_sleep)

        try:
            war = await self.get_current_war(war.clan_tag)
        except Forbidden:
            return

        if war.state == state_to_wait_for:
            self.dispatch('war_state_change', state_to_wait_for, war)
            return

        return await self._wait_for_state_change(state_to_wait_for, war)

    def _check_state_task_status(self, clan_tag):
        try:
            states = self._active_state_tasks[clan_tag]
        except KeyError:
            return

        return states.get('inWar'), states.get('warEnded')

    def _add_state_task(self, clan_tag, state, task):
        self._active_state_tasks[clan_tag][state] = task

    def _create_status_tasks(self, cached_war, war):
        if war.state == cached_war.state:
            return

        if war.state not in ['preparation', 'inWar', 'warEnded']:
            return

        in_war_task, war_ended_task = self._check_state_task_status(war.clan_tag)

        if not in_war_task or (war.start_time.time != cached_war.start_time.time):
            task = self.loop.create_task(self._wait_for_state_change('inWar', war))
            self._add_state_task(war.clan_tag, 'inWar', task)

        if not war_ended_task or (war.end_time.time != cached_war.end_time.time):
            task = self.loop.create_task(self._wait_for_state_change('inWar', war))
            self._add_state_task(war.clan_tag, 'warEnded', task)

    async def _update_wars(self):
        if not self._war_updates:
            return

        async for war in self.get_current_wars(self._war_updates, update_cache=False):
            cached_war = cache_current_wars.get(war.clan_tag)
            if not cached_war:
                cache_current_wars.add(war.clan_tag, war)
                continue

            if war == cached_war:
                cache_current_wars.add(war.clan_tag, war)
                continue

            self.dispatch('war_update', cached_war, war)

            await self._create_status_tasks(cached_war, war)

            if len(war._attacks) != len(cached_war._attacks):
                new_attacks = [n for n in war._attacks if n not in set(cached_war._attacks)]
                for attack in new_attacks:
                    self.dispatch('war_attack', attack, war)

            cache_current_wars.add(war.clan_tag, war)

    async def _update_players(self):
        if not self._player_updates:
            return

        async for player in self.get_players(self._player_updates, update_cache=False):
            cached_player = cache_search_players.get(player.tag)

            if not cached_player:
                cache_search_players.add(player.tag, player)
                continue

            if player == cached_player:
                continue

            self.dispatch('player_update', cached_player, player)

            if player.name != cached_player.name:
                self.dispatch('player_name_change', cached_player.name, player.name, player)
                cached_player._data['name'] = player.name

            if player.town_hall != cached_player.town_hall:
                self.dispatch('player_townhall_upgrade', cached_player.town_hall, player.town_hall, player)
                cached_player._data['townHallLevel'] = player.town_hall

            if player.builder_hall != cached_player.builder_hall:
                self.dispatch('player_builderhall_upgrade',
                              cached_player.builder_hall, player.builder_hall, player)
                cached_player._data['builderHallLevel'] = player.town_hall

            if player == cached_player:
                cache_search_players.add(player.tag, player)
                continue

            achievement_updates = [n for n in player._achievements if n not in set(cached_player._achievements)]
            troop_upgrades = [n for n in player.troops if n not in set(cached_player.troops)]
            spell_upgrades = [n for n in player.spells if n not in set(cached_player.spells)]
            hero_upgrades = [n for n in player.heroes if n not in set(cached_player.heroes)]

            for achievement in achievement_updates:
                old_achievement = get(cached_player._achievements, name=achievement.name)
                self.dispatch('player_achievement_update', old_achievement, achievement)
                cached_player._data['achievements'][achievement.name] = achievement._data

            for troop in troop_upgrades:
                old_troop = get(cached_player.troops, name=troop.name)
                self.dispatch('player_troop_upgrade', old_troop, troop, player)
                cached_player._data['troops'][troop.name] = troop._data

            for spell in spell_upgrades:
                old_spell = get(cached_player.spells, name=spell.name)
                self.dispatch('player_spell_upgrade', old_spell, spell, player)
                cached_player._data['spells'][spell.name] = spell._data

            for hero in hero_upgrades:
                old_hero = get(cached_player.heroes, name=hero.name)
                self.dispatch('player_hero_upgrade', old_hero, hero, player)
                cached_player._data['heroes'][hero.name] = hero._data

            if cached_player == player:
                cache_search_players.add(player.tag, player)
                continue

            self.dispatch('player_other_update', cached_player, player)

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

from .cache import Cache
from .clans import Clan, SearchClan
from .errors import Forbidden, NotFound
from .miscmodels import Location, League
from .http import HTTPClient
from .iterators import PlayerIterator, ClanIterator, ClanWarIterator, LeagueWarIterator, CurrentWarIterator
from .nest_asyncio import apply
from .players import Player, LeagueRankedPlayer, SearchPlayer
from .utils import get
from .wars import ClanWar, WarLog, LeagueWar, LeagueWarLogEntry, LeagueGroup

log = logging.getLogger(__name__)

LEAGUE_WAR_STATE = 'notInWar'
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


cache_search_clans = Cache()
cache_war_clans = Cache()

cache_search_players = Cache()
cache_war_players = Cache()

cache_clan_wars = Cache()
cache_war_logs = Cache()

cache_league_groups = Cache()
cache_league_wars = Cache()

cache_current_wars = Cache()

cache_locations = Cache()

cache_leagues = Cache()
cache_seasons = Cache()

cache_events = Cache()


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

    default_cache : function
        The :class:`function` to use for default cache initiation.
        If nothing is passed, this defaults to :func:`Client.default_cache()`.
        This function must have client as the first and only parameter.
        It **must not** be a coroutine.

        Example: ::

            def setup(client):
                client.edit_cache('players', 1024, 300)
                print('Set cache for players to max size 1024, expiry 30 seconds')

                client.edit_cache(extra_settings={'war': {'max_size': 1024, 'expiry': 300}}
                print('Set my second cache')

                return

            clash_client = coc.login('email', 'password', default_cache=setup)

    Attributes
    -----------
    loop : :class:`asyncio.AbstractEventLoop`
        The loop that is used for HTTP requests
    """
    __slots__ = ('loop', 'correct_key_count', 'key_names', 'throttle_limit',
                 'http', '_ready', '_cache_lookup', '_default_cache')

    def __init__(self, *, key_count: int=1,
                 key_names: str='Created with coc.py Client',
                 throttle_limit: int=10,
                 loop: asyncio.AbstractEventLoop=None,
                 default_cache=None):

        self.loop = loop or asyncio.get_event_loop()
        apply(self.loop)

        self.correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == self.correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(
                KEY_MINIMUM, KEY_MAXIMUM))

        self.key_names = key_names
        self.throttle_limit = throttle_limit

        self.http = None  # set in method login()
        self._ready = asyncio.Event(loop=loop)

        self._cache_lookup = {
            'cache_search_clans': cache_search_clans,
            'cache_war_clans': cache_war_clans,

            'cache_search_players': cache_search_players,
            'cache_war_players': cache_war_players,

            'cache_clan_wars': cache_clan_wars,
            'cache_war_logs': cache_war_logs,
            'cache_current_wars': cache_current_wars,

            'cache_league_groups': cache_league_groups,
            'cache_league_wars': cache_league_wars,

            'cache_locations': cache_locations,

            'cache_leagues': cache_leagues,
            'cache_seasons': cache_seasons
        }

        self._default_cache = default_cache or self.default_cache
        log.info('Clash of Clans client created')

        self._default_cache(self)
        log.debug('Cache has been set using %s', 'default cache' if not default_cache else 'custom cache')

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

        try:
            fctn = getattr(self, event_name)
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

    def _get_cache_from_name(self, name):
        try:
            return self._cache_lookup[str(name)]
        except KeyError:
            return None

    def default_cache(self, client):
        """The default cache initiation.

        This function is called on initiation of the :class:`Client`.

        The grouping and relevant max size and expiry are as follows:

        +-------------------------+------------+------------+-----------+
        |       Cache Name        | Cache Type |  Max Size  |  Expiry   |
        +=========================+============+============+===========+
        |``cache_search_clans``   | ``clan``   |   1024     | 1 hour    |
        +-------------------------+------------+------------+-----------+
        |``cache_war_logs``       | ``clan``   |   1024     | 1 hour    |
        +-------------------------+------------+------------+-----------+
        |``cache_current_wars``   | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_clan_wars``      | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_league_groups``  | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_league_wars``    | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_war_clans``      | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_war_players``    | ``war``    |   1024     | 0.5 hours |
        +-------------------------+------------+------------+-----------+
        |``cache_search_players`` | ``player`` |   1024     | 1 hour    |
        +-------------------------+------------+------------+-----------+
        |``cache_locations``      | ``static`` |   1024     | Never     |
        +-------------------------+------------+------------+-----------+
        |``cache_leagues``        | ``static`` |   1024     | Never     |
        +-------------------------+------------+------------+-----------+
        |``cache_seasons``        | ``static`` |   1024     | Never     |
        +-------------------------+------------+------------+-----------+

        """
        cache_search_clans._is_clan = True
        cache_war_logs._is_clan = True

        cache_clan_wars._is_war = True
        cache_current_wars._is_war = True
        cache_league_groups._is_war = True
        cache_league_wars._is_war = True
        cache_war_clans._is_war = True
        cache_war_players._is_war = True

        cache_search_players._is_player = True

        cache_locations._is_static = True
        cache_leagues._is_static = True
        cache_seasons._is_static = True

        clan_cache = (n for n in self._cache_lookup.values() if n._is_clan)
        player_cache = (n for n in self._cache_lookup.values() if n._is_player)
        war_cache = (n for n in self._cache_lookup.values() if n._is_war)
        static_cache = (n for n in self._cache_lookup.values() if n._is_static)

        for n in clan_cache:
            n.clear(max_size=1024, ttl=3600)  # ttl = hour
        for n in player_cache:
            n.clear(max_size=1024, ttl=3600)  # ttl = hour
        for n in war_cache:
            n.clear(1024, ttl=1800)  # ttl = half hour
        for n in static_cache:
            n.clear(1024, None)  # ttl = never expire

    def edit_cache(self, cache_group: str=None, max_size: int=None, expiry: int=None, extra_settings: dict=None):
        """Edit the cache from the default settings.

        Alternatively, this function could be passed into the ``default_cache`` parameter of :class:`Client`,
        as follows: ::

            def cache(client):
                return client.edit_cache('players', 1024, 300)

            coc_client = coc.login('email', 'password', default_cache=cache)


        Parameters
        -----------
        cache_group : str
            This could either be a cache name or cache group type.
            See all names and types in :meth:`Client.default_cache`.
        max_size : int
            The max size to set for ``cache_group`` passed.
        expiry : int
            The expiry of cache in seconds for ``cache_group`` passed.
        extra_settings : dict
            A dictionary of extra settings for advanced usage.
            Example: ::

                # format:
                {cache_group: {'max_size': int, 'expiry': int}, ...}
                # eg:
                {'clan': {'max_size': 1024, 'expiry': 30}, 'player': {1024, 300}}

            Alternatively, you could call this function multiple times for each type you want to change.

        """
        clan_cache = (n for n in self._cache_lookup.values() if n._is_clan)
        player_cache = (n for n in self._cache_lookup.values() if n._is_player)
        war_cache = (n for n in self._cache_lookup.values() if n._is_war)
        static_cache = (n for n in self._cache_lookup.values() if n._is_static)
        all_cache = (n for n in self._cache_lookup.values())

        lookup = {
            'clan': clan_cache,
            'player': player_cache,
            'war': war_cache,
            'static': static_cache,
            'all': all_cache
        }

        def f(name):
            try:
                c = lookup[str(name)]
            except KeyError:
                try:
                    c = [self._cache_lookup[str(name)]]
                except KeyError:
                    return []
            return c

        for n in f(cache_group):
            n.clear(max_size=max_size, ttl=expiry)

        if not extra_settings:
            return

        for k, v in extra_settings.items():
            for cache in f(k):
                try:
                    cache.clear(max_size=v[0], ttl=v[1])
                except (IndexError, KeyError):
                    continue

    async def reset_keys(self, number_of_keys: int=None):
        """Manually reset any number of keys.

        Under normal circumstances, this method should not need to be called.

        Parameters
        -----------
        number_of_keys : int
            The number of keys to reset. Defaults to None - all keys.
        """
        self._ready.clear()
        num = number_of_keys or len(self.http._keys)
        keys = self.http._keys
        for i in range(num):
            await self.http.reset_key(keys[i])
        self._ready.set()

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
                wars.append(LeagueWarLogEntry(data=n, clan_tag=clan_tag, http=self.http))
                continue

            # for earlier logs this is distinguished by no opponent tag (result called `tie`)
            if n.get('opponent', {}).get('tag', None) is None:
                wars.append(LeagueWarLogEntry(data=n, clan_tag=clan_tag, http=self.http))
                continue

            wars.append(WarLog(data=n, clan_tag=clan_tag, http=self.http))

        if update_cache:
            cache_war_logs.add(wars[0].clan.tag, wars)

        return wars

    @cache_clan_wars.get_cache()
    async def get_clan_war(self, clan_tag: str, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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
        r = await self.http.get_clan_current_war(clan_tag)
        return ClanWar(data=r, clan_tag=clan_tag, http=self.http)

    def get_clan_wars(self, clan_tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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

        Returns
        --------
        :class:`coc.iterators.WarIterator` of :class:`ClanWar`
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return ClanWarIterator(self, clan_tags, cache, fetch, update_cache)

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

    def get_league_wars(self, war_tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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

        Returns
        --------
        :class:`coc.iterators.LeagueWarIterator` of :class:`LeagueWar`
        """
        if not isinstance(war_tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return LeagueWarIterator(self, war_tags, cache, fetch, update_cache)

    @cache_current_wars.get_cache()
    async def get_current_war(self, clan_tag: str, *, league_war: bool=True,
                              cache: bool=False, fetch: bool=True, update_cache: bool=True):
        """Retrieve a clan's current war.

        Unlike ``Client.get_clan_war`` or ``Client.get_league_war``, this method will search for a regular war,
        and if the clan is in ``notInWar`` state, search for a current league war.

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
        These can be differentiated by through an ``isinstance(..)`` method, or by comparing ``type`` attributes.

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

        if league_group.state == 'preparation':
            return get_war

        round_tags = league_group.rounds[-1]

        async for war in self.get_league_wars(round_tags, cache=cache, fetch=fetch, update_cache=update_cache):
            if war.clan_tag == clan_tag:
                return war
        else:
            return None

    def get_current_wars(self, clan_tags: Iterable, cache: bool=False, fetch: bool=True, update_cache: bool=True):
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

        Returns
        --------
        :class:`coc.iterators.CurrentWarIterator` of either :class:`LeagueWar` or :class:`ClanWar`, or both.
        """
        if not isinstance(clan_tags, Iterable):
            raise TypeError('Tags are not an iterable.')

        return CurrentWarIterator(client=self, tags=clan_tags, cache=cache, fetch=fetch, update_cache=update_cache)

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
        super().__init__(**options)
        apply(self.loop)
        self._setup()
        self._cache_lookup['cache_events'] = cache_events

    def _setup(self):
        self._clan_updates = []
        self._player_updates = []
        self._war_updates = []

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
        for n in self._updater_tasks.values():
            n.add_done_callback(self._task_callback_check)

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

    @cache_events.events_cache()
    def dispatch(self, event_name: str, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        for event in self.extra_events.get(event_name, []):
            asyncio.ensure_future(self._run_event(event_name, event, *args, **kwargs), loop=self.loop)

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

        if name == 'on_event_error':
            super().event(fctn)
            return

        if name in self.extra_events:
            self.extra_events[name].append(fctn)
        else:
            self.extra_events[name] = [fctn]

        log.info('Successfully registered %s event', name)
        return fctn

    def add_events(self, *fctns, function_dicts: dict=None):
        """Provides an alternative method to adding events.

        You can either provide functions as named args or as a dict of {name: function...} values.

        Example
        --------

        .. code-block:: python3

            client.add_events(on_member_update, on_clan_update, on_war_attack)
            # or, using a dict:
            client.add_events(function_dicts={'on_member_update': on_update, 'on_clan_update': on_update_2})

        Parameters
        -----------
        fctns : function
            Named args of functions to register. The name of event is dictated by function name.
        function_dicts : dict
            Dictionary of ``{'event_name': function}`` values.
        """
        for f in fctns:
            self.event(f)
        if function_dicts:
            for n, f in function_dicts.items():
                self.event(f, name=n)

    def run_forever(self):
        """A blocking call which runs the loop and script.

        This is useful if you have no other clients to deal
        with and just wish to run the script and receive updates indefinately.

        Roughly equivilant to:

        .. code-block:: python3

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
        except (Exception, BaseException):
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
        self._clan_updates.extend(n for n in tags)

        if member_updates is True:
            async for clan in self.get_clans(tags):
                self.add_player_update((n.tag for n in clan._members), retry_interval=retry_interval)

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
        self._war_updates.extend(n for n in tags)

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
        self._player_updates.extend(n for n in tags)

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._player_retry_interval = retry_interval

    def start_updates(self, event_type='all'):
        """Starts an, or all, events.

        .. note::

            This method **must** be called before any events are run.

        The lookup for event_name is as follows:

        +-----------------------------------+----------------------+
        |     Event Name                    | Event Type           |
        +-----------------------------------+----------------------+
        | ``on_clan_update``                | ``clan``             |
        +-----------------------------------+----------------------+
        | ``on_clan_member_join``           | ``clan``             |
        +-----------------------------------+----------------------+
        | ``on_clan_member_leave``          | ``clan``             |
        +-----------------------------------+----------------------+
        | ``on_clan_settings_update``       | ``clan``             |
        +-----------------------------------+----------------------+
        | ``on_war_update``                 | ``war``              |
        +-----------------------------------+----------------------+
        | ``on_war_attack``                 | ``war``              |
        +-----------------------------------+----------------------+
        | ``on_war_state_change``           | ``war``              |
        +-----------------------------------+----------------------+
        | ``on_player_update``              | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_name_change           | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_townhall_upgrade``    | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_builderhall_upgrade`` | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_achievement_update``  | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_troop_upgrade``       | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_spell_upgrade``       | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_troop_upgrade``       | ``player``           |
        +-----------------------------------+----------------------+
        | ``on_player_other_update``        | ``player``           |
        +-----------------------------------+----------------------+

        Parameters
        -----------
        event_type : str
            See above for which string corresponds to events.
            Defaults to 'all'

        Example
        --------
        .. code-block:: python3

            client.start_updates('clan')
            # or, for all events:
            client.start_updates('all')

        """
        lookup = {
            'clan': [self._clan_update_event, [cache_current_wars]],
            'player': [self._player_update_event, [cache_search_players]],
            'war': [self._war_update_event, [cache_current_wars, cache_clan_wars, cache_league_wars]]
        }
        if event_type == 'all':
            events = lookup.values()
        else:
            events = [lookup[event_type]]

        for e in events:
            e[0].set()
            for c in e[1]:
                c.clear(1024, None)

    def stop_updates(self, event_type='all'):
        """Stops an, or all, events.

        .. note::
            This method **must** be called in order to stop any events.

        Parameters
        -----------
        event_type : str
            See :meth:`EventsClient.start_updates` for which string corresponds to events.
            Defaults to 'all'

        Example
        --------
        .. code-block:: python3

            client.stop_updates('clan')
            # or, for all events:
            client.stop_updates('all')

        """

        lookup = {
            'clan': [self._clan_update_event, [cache_current_wars]],
            'player': [self._player_update_event, [cache_search_players]],
            'war': [self._war_update_event, [cache_current_wars, cache_clan_wars, cache_league_wars]]
        }
        if event_type == 'all':
            events = lookup.values()
        else:
            events = [lookup[event_type]]

        for e in events:
            e[0].clear()
            for c in e[1]:
                c.clear(1024, None)

    def _dispatch_batch_updates(self, key_name):
        keys = cache_events.cache.keys()
        if not keys:
            return
        events = [n for n in keys if n.startswith(key_name)]
        self.dispatch(f'{key_name}_batch_updates', [cache_events.cache.pop(n, None) for n in events])

    def _task_callback_check(self, result):
        if not result.done():
            return
        if result.cancelled():
            log.info('Task %s was cancelled', str(result))
            return

        exception = result.exception()
        if not exception:
            return

        log.warning('Task raised an exception that was unhandled %s. Restarting the task.', exception)

        lookup = {
            'clan': self._clan_updater,
            'player': self._player_updater,
            'war': self._war_updater
                  }

        for k, v in self._updater_tasks.items():
            if v != result:
                continue
            self._updater_tasks[k] = self.loop.create_task(lookup[k])
            self._updater_tasks[k].add_done_callback(self._task_callback_check)

    async def _war_updater(self):
        try:
            while self.loop.is_running():
                await self._war_update_event.wait()
                await asyncio.sleep(self._war_retry_interval)
                await self._update_wars()
                self._dispatch_batch_updates('on_war')
        except (Exception, BaseException):
            await self.on_event_error('on_war_update')
            return await self._war_updater()

    async def _clan_updater(self):
        try:
            while self.loop.is_running():
                await self._clan_update_event.wait()
                await asyncio.sleep(self._war_retry_interval)
                await self._update_clans()
                self._dispatch_batch_updates('on_clan')
        except (Exception, BaseException):
            await self.on_event_error('on_clan_update')
            return await self._clan_updater()

    async def _player_updater(self):
        try:
            while self.loop.is_running():
                await self._player_update_event.wait()
                await asyncio.sleep(self._player_retry_interval)
                await self._update_players()
                self._dispatch_batch_updates('on_player')
        except (Exception, BaseException):
            await self.on_event_error('on_player_update')
            return await self._player_updater()

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
            self.dispatch('on_war_state_change', state_to_wait_for, war)
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

        async for war in self.get_current_wars(self._war_updates, cache=False, update_cache=False):
            cached_war = cache_current_wars.get(war.clan_tag)

            if not cached_war:
                cache_current_wars.add(war.clan_tag, war)
                continue

            if war == cached_war:
                continue

            self.dispatch('on_war_update', cached_war, war)

            self._create_status_tasks(cached_war, war)

            if len(war.attacks) != len(cached_war.attacks):
                if not war._attacks:
                    continue  # if there are no attacks next line will raise TypeError.. we're not in war anymore anyway
                if not cached_war._attacks:
                    new_attacks = war.attacks
                else:
                    new_attacks = [n for n in war._attacks if n not in set(cached_war._attacks)]

                for attack in new_attacks:
                    self.dispatch('on_war_attack', attack, war)

            cache_current_wars.add(war.clan_tag, war)

    async def _update_players(self):
        if not self._player_updates:
            return

        async for player in self.get_players(self._player_updates, cache=False, update_cache=False):
            cached_player = cache_search_players.get(player.tag)

            if not cached_player:
                cache_search_players.add(player.tag, player)
                continue

            if player == cached_player:
                continue

            self.dispatch('on_player_update', cached_player, player)

            # name
            if player.name != cached_player.name:
                self.dispatch('on_player_name_change', cached_player.name, player.name, player)

            # town/builder halls
            if player.town_hall != cached_player.town_hall:
                self.dispatch('on_player_townhall_upgrade', cached_player.town_hall, player.town_hall, player)
            if player.builder_hall != cached_player.builder_hall:
                self.dispatch('on_player_builderhall_upgrade',
                              cached_player.builder_hall, player.builder_hall, player)

            # best trophies/versus/war stars
            if player.best_trophies != cached_player.best_trophies:
                self.dispatch('on_player_best_trophies_change',
                              cached_player.best_trophies, player.best_trophies, player)
            if player.best_versus_trophies != cached_player.best_versus_trophies:
                self.dispatch('on_player_best_versus_trophies_change',
                              cached_player.best_versus_trophies, player.best_versus_trophies, player)
            if player.war_stars != cached_player.war_stars:
                self.dispatch('on_player_war_stars_change', cached_player.war_stars, player.war_stars, player)

            # attacks win/defense/versus
            if player.attack_wins != cached_player.attack_wins:
                self.dispatch('on_player_attack_wins_change', cached_player.attack_wins, player.attack_wins, player)
            if player.defense_wins != cached_player.defense_wins:
                self.dispatch('on_player_defense_wins_change', cached_player.defense_wins, player.defense_wins, player)
            if player.versus_attacks_wins != cached_player.versus_attacks_wins:
                self.dispatch('on_player_versus_attacks_change',
                              cached_player.versus_attacks_wins, player.versus_attacks_wins, player)

            # trophies + league
            if player.trophies != cached_player.trophies:
                self.dispatch('on_player_trophies_change', cached_player.trophies, player.trophies, player)
            if player.league != cached_player.league:
                self.dispatch('on_player_league_change', cached_player.league, player.league, player)

            # clan stuff: role, donations, received, rank and prev. rank
            if player.role != cached_player.role:
                self.dispatch('on_player_role_change', cached_player.role, player.role, player)
            if player.donations != cached_player.donations:
                self.dispatch('on_player_donations_change', cached_player.donations, player.donations, player)
            if player.received != cached_player.received:
                self.dispatch('on_player_received_change', cached_player.received, player.received, player)
            if player.clan_rank != cached_player.clan_rank:
                self.dispatch('on_player_clan_rank_change', cached_player.clan_rank, player.clan_rank, player)
            if player.clan_previous_rank != cached_player.clan_previous_rank:
                self.dispatch('on_player_clan_previous_rank_change',
                              cached_player.clan_previous_rank, player.clan_previous_rank, player)

            achievement_updates = (n for n in player.achievements if n not in set(cached_player.achievements))
            troop_upgrades = (n for n in player.troops if n not in set(cached_player.troops))
            spell_upgrades = (n for n in player.spells if n not in set(cached_player.spells))
            hero_upgrades = (n for n in player.heroes if n not in set(cached_player.heroes))

            for achievement in achievement_updates:
                old_achievement = get(cached_player.achievements, name=achievement.name)
                self.dispatch('on_player_achievement_update', old_achievement, achievement, player)

            for troop in troop_upgrades:
                old_troop = get(cached_player.troops, name=troop.name)
                self.dispatch('on_player_troop_upgrade', old_troop, troop, player)

            for spell in spell_upgrades:
                old_spell = get(cached_player.spells, name=spell.name)
                self.dispatch('on_player_spell_upgrade', old_spell, spell, player)

            for hero in hero_upgrades:
                old_hero = get(cached_player.heroes, name=hero.name)
                self.dispatch('on_player_hero_upgrade', old_hero, hero, player)

    async def _update_clans(self):
        if not self._clan_updates:
            return

        async for clan in self.get_clans(self._clan_updates, cache=False, update_cache=False):
            cached_clan = cache_search_clans.get(clan.tag)
            if not cached_clan:
                cache_search_clans.add(clan.tag, clan)
                continue

            if clan == cached_clan:
                continue

            self.dispatch('on_clan_update', cached_clan, clan)

            if clan.member_count != cached_clan.member_count:
                new_members = [n for n in clan.members if n.tag not in set(n.tag for n in cached_clan.members)]
                for mem_join in new_members:
                    self.dispatch('on_clan_member_join', mem_join, clan)

                old_members = [n for n in cached_clan.members if n.tag not in set(n.tag for n in clan.members)]
                for mem_left in old_members:
                    self.dispatch('on_clan_member_leave', mem_left, clan)

            if clan.members != cached_clan.members:
                await self._update_clan_members(cached_clan, clan)

            # settings
            if clan.level != cached_clan.level:
                self.dispatch('on_clan_level_change', cached_clan.level, clan.level, clan)
            if clan.description != cached_clan.description:
                self.dispatch('on_clan_description_change', cached_clan.description, clan.description, clan)
            if clan.public_war_log != cached_clan.public_war_log:
                self.dispatch('on_clan_public_war_log_change', cached_clan.public_war_log,
                              clan.public_war_log, clan)
            if clan.type != cached_clan.type:
                self.dispatch('on_clan_type_change', cached_clan.type, clan.type, clan)
            if clan.badge != cached_clan.badge:
                self.dispatch('on_clan_badge_change', cached_clan.badge, clan.badge, clan)
            if clan.required_trophies != cached_clan.required_trophies:
                self.dispatch('on_clan_required_trophies_change',
                              cached_clan.required_trophies, clan.required_trophies, clan)
            if clan.war_frequency != cached_clan.war_frequency:
                self.dispatch('on_clan_war_frequency_change', cached_clan.war_frequency, clan.war_frequency, clan)

            # war win/loss/tie/streak
            if clan.war_win_streak != cached_clan.war_win_streak:
                self.dispatch('on_clan_war_win_streak_change', cached_clan.war_win_streak, clan.war_win_streak,
                              clan)
            if clan.war_wins != cached_clan.war_wins:
                self.dispatch('on_clan_war_win_change', cached_clan.war_wins, clan.war_wins, clan)
            if clan.war_ties != cached_clan.war_ties:
                self.dispatch('on_clan_war_tie_change', cached_clan.war_ties, clan.war_ties, clan)
            if clan.war_losses != cached_clan.war_losses:
                self.dispatch('on_clan_war_loss_change', cached_clan.war_losses, clan.war_losses, clan)

            cache_search_clans.add(clan.tag, clan)

    async def _update_clan_members(self, cached_clan, clan):
        members = [n for n in clan.members if n != cached_clan.get_member(tag=n.tag)]
        for m in members:
            cached_member = cached_clan.get_member(tag=m.tag)
            if not cached_member:
                continue

            if m.name != cached_member.name:
                self.dispatch('on_clan_member_name_change', cached_member.name, m.name, m, clan)
            if m.donations != cached_member.donations:
                self.dispatch('on_clan_member_donation', cached_member.donations, m.donations, m, clan)
            if m.received != cached_member.received:
                self.dispatch('on_clan_member_received', cached_member.received, m.received, m, clan)
            if m.role != cached_member.role:
                self.dispatch('on_clan_member_role_change', cached_member.role, m.role, m, clan)
            if m.clan_rank != cached_member.clan_rank:
                self.dispatch('on_clan_member_rank_change', cached_member.clan_rank, m.clan_rank, m, clan)
            if m.level != cached_member.level:
                self.dispatch('on_clan_member_level_change', cached_member.level, m.level, m, clan)


EventsClient.__doc__ = Client.__doc__

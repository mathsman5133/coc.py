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


from .cache import Cache
from .http import HTTPClient
from .dataclasses import *

log = logging.getLogger(__name__)

LEAGUE_WAR_STATE = 'notInWar'
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


class Client:
    """
    This is the client connection used to interact with the Clash of Clans API.

    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html

    Parameters
    -------------

    email: :class:`str`
        Your password email from https://developer.clashofclans.com
        This is used when updating the key automatically if your IP changes

    password: :class:`str`
        Your password login from https://developer.clashofclans.com
        This is used when updating the key automatically if your IP changes

    key_count: Optional[:class:`int`]
        The amount of keys to use for this client. Maximum of 10.
        Defaults to 1

    key_names: Optional[:class:`str`]
        Default name for keys created to use for this client.
        All keys created or to be used with this client must
        have this name.

        Defaults to "Created with coc.py Client"

    throttle_limit: Optional[:class:`int`]
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

    loop: Optional[event loop]
        The `event loop` to use for HTTP requests.
        An ``asyncio.get_event_loop()`` will be used if none is passed

    Attributes
    -----------
    loop
        The `event_loop`_ that is used for HTTP requests

    """
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

    def __init__(self, email, password, key_count=1,
                 key_names='Created with coc.py Client',
                 throttle_limit=10,
                 loop=None):

        self.loop = loop or asyncio.get_event_loop()
        correct_key_count = max(min(KEY_MAXIMUM, key_count), KEY_MINIMUM)

        if not key_count == correct_key_count:
            raise RuntimeError("Key count must be within {}-{}".format(
                KEY_MINIMUM, KEY_MAXIMUM))

        self.http = HTTPClient(client=self, email=email, password=password,
                               key_names=key_names, loop=self.loop,
                               key_count=correct_key_count,
                               throttle_limit=throttle_limit)

        log.info('Clash of Clans API client created')

    async def close(self):
        """
        Closes the HTTP connection
        """
        log.info('Clash of Clans client logging out...')
        await self.http.close()

    async def on_key_reset(self, new_key):
        """Event: called when one of the client's keys are reset.

        By default this does nothing.

        Example
        ---------

        You can manually override this by either:

        Subclassing Client:

        .. code-block:: python3

            class Client(coc.Client):
                def __init__(self, key, email, password):
                    super().__init__(email, password, key_count=1,
                                 key_names='Created with coc.py Client', loop=None)

                def on_key_reset(key):
                    print('My new key is {}'.format(key))

        Using the event decorator:

        .. code-block:: python3

            @client.event()
            async def on_key_reset(key):
                print('My new key is {}'.format(key))

        :param new_key: :class:`str` The new key
        """
        pass

    def event(self, fctn):
        """A decorator that registers an event.

        The only event at present is :func:`on_key_reset`.

        This could be a coro or regular function.

        Example
        --------

        .. code-block:: python3

            @client.event()
            async def on_key_reset(key):
                print('My new key is {}'.format(key))
        """
        setattr(self, fctn.__name__, fctn)
        log.info('Successfully registered %s event', fctn.__name__)
        return fctn

    def dispatch(self, event_name, *args, **kwargs):
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
                event(*args, **kwargs)

    def set_cache(self, cache_to_edit, max_size=128, ttl=None):
        cache_type = getattr(self, cache_to_edit)
        if not cache_type:
            raise ValueError('{} is not a cached data class'.format(cache_to_edit))

        cache = Cache(max_size=max_size, ttl=ttl)
        setattr(self, cache_to_edit, cache)

    async def search_clans(self, *, name: str=None, war_frequency: str=None,
                           location_id: int = None, min_members: int=None, max_members: int=None,
                           min_clan_points: int = None, min_clan_level: int=None, limit: int=None,
                           before: int=None, after: int=None
                           ):
        """Search all clans by name and/or filtering the results using various criteria.

        At least one filtering criteria must be defined and if name is used as part
        of search, it is required to be at least three characters long.

        :param name: Optional[:class:`str`]
        :param war_frequency: Optional[:class:`str`]
        :param location_id: Optional[:class:`int`]
        :param min_members: Optional[:class:`int`]
        :param max_members: Optional[:class:`int`]
        :param min_clan_points: Optional[:class:`int`]
        :param min_clan_level: Optional[:class:`int`]
        :param limit: Optional[:class:`int`]

        :raise HTTPException: no options were passed

        :return: :class:`list` of all :class:`SearchClan` found

        """

        r = await self.http.search_clans(name=name, warFrequency=war_frequency, locationId=location_id,
                                         minMembers=min_members, maxMembers=max_members, minClanPoints=min_clan_points,
                                         minClanLevel=min_clan_level, limit=limit, before=before, after=after)

        clans = list(SearchClan(data=n) for n in r.get('items', []))

        return clans

    @cache_search_clans.get_cache()
    async def get_clan(self, tag, cache=False, fetch=True):
        """Get information about a single clan by clan tag. Clan tags can be found using clan search operation.

        :param tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`SearchClan`
        """
        r = await self.http.get_clan(tag)
        return SearchClan(data=r)

    async def get_clans(self, tags, cache=False, fetch=True):
        """Get information about multiple clans by clan tag. Refer to `Client.get_clan` for more information.
        
        Example
        ---------

        .. code-block:: python3
        
            tags = [...]
            async for clan in Client.get_clans(tags):
                print(clan)
                
        :param tags: :class:`collections.Iterable` The tags to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`SearchClan`
        """
        
        tags = iter(tags)
        
        for tag in tags:
            if cache:
                c = self.cache_search_clans.get(tag)
                if c:
                    yield c
                if fetch is False:
                    yield None

            r = await self.http.get_clan(tag)
            c = SearchClan(data=r)
            self.cache_search_clans.add(c.tag, c)

            yield c

    async def get_members(self, clan_tag, cache=False, fetch=True):
        """List clan members. This is equivilant to `Client.get_clan('tag').members.

        :param clan_tag: :class:`str` The clan tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`list` of :class:`BasicPlayer`
        """
        if cache:
            c = self.cache_search_clans.get(clan_tag)
            if c:
                return c.members

            if fetch is False:
                return None

        r = await self.http.get_clan(clan_tag)
        clan = SearchClan(data=r)

        self.cache_search_clans.add(clan.tag, clan)

        return clan.members

    @cache_war_logs.get_cache()
    async def get_warlog(self, clan_tag, cache=False, fetch=True):
        """Retrieve clan's clan war log

        :param clan_tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`list` of either :class:`WarLog` or :class:`LeagueWarLogEntry`, according to which war it is,

        """
        r = await self.http.get_clan_warlog(clan_tag)

        wars = []
        for n in r.get('items', []):
            # lately war log entries for sccwl can be distinguished by a `null` result
            if n.get('result') is None:
                wars.append(LeagueWarLogEntry(data=n))
                continue

            # for earlier logs this is distinguished by no opponent tag (result called `tie`)
            if n.get('opponent', {}).get('tag', None) is None:
                wars.append(LeagueWarLogEntry(data=n))
                continue

            wars.append(WarLog(data=n))

        self.cache_war_logs.add(wars[0].clan.tag, wars)

        return wars

    @cache_current_wars.get_cache()
    async def get_current_war(self, clan_tag, cache=False, fetch=True):
        """
        Retrieve information about clan's current clan war

        :param clan_tag: :class:`str` The clan tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`CurrentWar`
        """
        r = await self.http.get_clan_current_war(clan_tag)
        return CurrentWar(data=r)
    
    async def get_current_wars(self, clan_tags, cache=False, fetch=True):
        """
        Retrieve information multiple clan's current clan wars
        
        Example
        ---------

        .. code-block:: python3
        
            tags = [...]
            async for clan_war in Client.get_current_wars(tags):
                print(clan_war.opponent)

        :param clan_tags: :class:`collections.Iterable` The clan tags to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`CurrentWar`
        """
        
        clan_tags = iter(clan_tags)
        
        for clan_tag in clan_tags:
            if cache:
                wl = self.cache_current_wars.get(clan_tag)
                if wl:
                    yield wl

                if fetch is False:
                    yield None

            r = await self.http.get_clan_current_war(clan_tag)
            war = CurrentWar(data=r)

            self.cache_current_wars.add(war.clan.tag, war)
            yield war

    @cache_league_groups.get_cache()
    async def get_league_group(self, clan_tag, cache=False, fetch=True):
        """Retrieve information about clan's current clan war league group

        :param clan_tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`LeagueGroup`
        """
        r = await self.http.get_clan_war_league_group(clan_tag)
        return LeagueGroup(data=r)

    @cache_league_wars.get_cache()
    async def get_league_war(self, war_tag, cache=False, fetch=True):
        """
        Retrieve information about a clan war league war

        :param war_tag: :class:`str` The tag of league war to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`LeagueWar`
        """
        r = await self.http.get_cwl_wars(war_tag)
        return LeagueWar(data=r)

    # locations
    async def search_locations(self, *, limit: int=10,
                               before: int=None, after: int=None):
        """
        List all available locations

        :param limit: Optional[:class:`int`] Number of items to fetch. Default is 10

        :raise HTTPException: no options were passed

        :return: :class:`list` of all :class:`Location` found

        """

        data = await self.http.search_locations(limit=limit, before=before, after=after)

        locations = list(Location(data=n) for n in data['items'])

        for n in locations:
            self.cache_locations.add(n.id, n)

        return locations

    @cache_locations.get_cache()
    async def get_location(self, location_id, cache=False, fetch=True):
        """
        Get information about specific location

        :param location_id: :class:`int` The location ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`Location`
        """
        r = await self.http.get_location(location_id)
        return Location(data=r)

    async def get_location_clan(self, location_id, *, limit: int=None,
                                before: int=None, after: int=None):
        """
        Get clan rankings for a specific location


        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :return: :class:`Clan`
        """

        r = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after)
        return list(Clan(data=n) for n in r['items'])

    async def get_location_players(self, location_id, *, limit: int=None,
                                   before: int=None, after: int=None):
        """
        Get player rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :return: :class:`Player`
        """
        r = await self.http.get_location_players(location_id, limit=limit, before=before, after=after)
        return list(Player(data=n) for n in r['items'])

    async def get_location_clans_versus(self, location_id, *, limit: int=None,
                                        before: int=None, after: int=None):
        """
        Get clan versus rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :return: :class:`Clan`
        """
        r = await self.http.get_location_clans_versus(location_id, limit=limit, before=before, after=after)
        return list(Clan(data=n) for n in r['items'])

    async def get_location_players_versus(self, location_id, *, limit: int = None,
                                          before: int = None, after: int = None):
        """
        Get player versus rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :return: :class:`Player`
        """
        r = await self.http.get_location_players_versus(location_id, limit=limit, before=before, after=after)
        return list(Player(data=n) for n in r['items'])

    # leagues

    async def search_leagues(self, *, limit: int=None, before: int=None, after: int=None):
        """
        Get list of leagues.

        :param limit: Optional[:class:`int`] Number of items to fetch. Default is 10

        :raise HTTPException: no options were passed

        :return: :class:`list` of all :class:`League` found

        """
        r = await self.http.search_leagues(limit=limit, before=before, after=after)
        leagues = list(League(data=n) for n in r['items'])

        for n in leagues:
            self.cache_leagues.add(n.id, n)

        return leagues

    @cache_leagues.get_cache()
    async def get_league(self, league_id, cache=False, fetch=True):
        """
        Get league information

        :param league_id: :class:`str` The ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`League`
        """
        r = await self.http.get_league(league_id)
        return League(data=r)

    async def get_seasons(self, league_id):
        """Get league seasons. Note that league season information is available only for Legend League.

        :param league_id: :class:`str` The league ID to search for

        :return: :class:`dict`

        In the form

        .. code-block:: json

            {
                "id": "string"
            }

        where `id` is the season ID
        """
        r = await self.http.get_league_seasons(league_id)
        return r['items']

    async def get_season_rankings(self, league_id, season_id, cache=False, fetch=True):
        """Get league season rankings.
        Note that league season information is available only for Legend League.

        :param league_id: :class:`str` The league ID to search for
        :param season_id: :class:`str` The season ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`list` of :class:`LeagueRankedPlayer`
        """
        if cache:
            try:
                data = self.cache_seasons.get(league_id)[season_id]
                if data:
                    return data

            except KeyError:
                pass

            if fetch is False:
                return None

        r = await self.http.get_league_season_info(league_id, season_id)
        players = list(LeagueRankedPlayer(data=n) for n in r.get('items', []))

        self.cache_seasons.add(league_id, {season_id: players})

        return players

    # players
    @cache_search_players.get_cache()
    async def get_player(self, player_tag, cache=False, fetch=True):
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        :param player_tag: :class:`str` The player tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`SearchPlayer`
        """
        r = await self.http.get_player(player_tag)
        return SearchPlayer(data=r)

    async def get_players(self, player_tags, cache=False, fetch=True):
        """Get information about a multiple players by player tag.
        Player tags can be found either in game or by from clan member lists.
        
        Example
        ---------

        .. code-block:: python3
        
            tags = [...]
            async for player in Client.get_players(tags):
                print(player)

        :param player_tags: :class:`collections.Iterable` The player tags to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`SearchPlayer`
        """
        
        player_tags = iter(player_tags)
        
        for player_tag in player_tags:
            if cache:
                data = self.cache_search_players.get(player_tag)
                if data:
                    yield data

                if fetch is False:
                    yield None

            r = await self.http.get_player(player_tag)
            p = SearchPlayer(data=r)
            self.cache_search_players.add(p.tag, p)

            yield p


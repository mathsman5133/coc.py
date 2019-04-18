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

import json as json_pckg

from typing import Union

from .http import HTTPClient
from .dataclasses import *

log = logging.getLogger(__name__)

LEAGUE_WAR_STATE = 'notInWar'


def check_json(clss, obj, json_bool):
    if isinstance(obj, list):
        to_return = []
        for n in obj:
            to_return.append(check_json(clss, n, json_bool))
        return to_return

    if isinstance(obj, clss) and json_bool is False:
        return obj

    if isinstance(obj, clss) and json_bool is True:
        return json_pckg.dumps(obj._data)

    if json_pckg is False:
        return clss(data=obj)

    return json_pckg.loads(obj)


def other_check(clss, obj, json_bool):
    if json_bool:
        return json_pckg.loads(obj.get('items', {}))

    return list(clss(data=n) for n in obj['items'])


class Client:
    """
    This is the client connection used to interact with the Clash of Clans API.

    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html

    Parameters
    -------------
    tokens: Union[:class:`str`, :class:`list`]
        The authentication tokens. These can be found on the developers page at
        https://developer.clashofclans.com
        Defaults to None, if tokens is None, then the client will attempt to
        retrieve them from the API. email and password will be required.

    loop: Optional[event loop]
        The `event loop`_ to use for HTTP requests.
        An ``asyncio.get_event_loop()`` will be used if none is passed

    email: Optional[:class:`str`]
        Your password email from https://developer.clashofclans.com
        This is used when updating the token automatically if your IP changes

        If `update_tokens` is set to ``True``, this must be passed.

    password: Optional[:class:`str`]
        Your password login from https://developer.clashofclans.com
        This is used when updating the token automatically if your IP changes

        If `update_tokens` is set to ``True``, this must be passed.

    update_tokens: Optional[:class:`bool`]
        This indicates whether the client should by default update your API Token
        when your IP Adress changes.

        More can be found on dynamic IP Adresses this API uses at:
            https://developer.clashofclans.com

        If an invalid token is passed and this is set to false, an ``InvalidToken``
        error will be raised.

        If this is ``True``, ``email`` and ``password`` parameters must be set.

    Attributes
    -----------
    loop
        The `event_loop`_ that is used for HTTP requests

    """

    def __init__(self, tokens=None, loop=None, email=None, password=None, update_tokens=False):
        self.loop = self.loop = loop or asyncio.get_event_loop()
        has_auth = not(password or email)
        
        if tokens:
            if isinstance(tokens, str): tokens = [tokens]
            elif isinstance(tokens, list): pass
            else: raise RuntimeError('tokens must be either a str or list of str tokens')
        else:
            if not has_auth:
                raise RuntimeError('An email and password must be set if no tokens are provided')

        if update_tokens and :
                raise RuntimeError('An email and password must be set if update_tokens is True')

        self.http = HTTPClient(client=self, tokens=tokens, loop=self.loop, email=email,
                               password=password, update_tokens=update_tokens)
        log.info('Clash of Clans API client created')
        self._add_cache()
        log.debug('Added cache')

    async def close(self):
        """
        Closes the HTTP connection
        """
        log.info('Clash of Clans client logging out...')
        await self.http.close()

    async def on_token_reset(self, new_token):
        """Event: called when the client's token is reset.

        By default this does nothing.

        Example
        ---------

        You can manually override this by either:

        Subclassing Client:

        .. code-block:: python3

            class Client(coc.Client):
                def __init__(self, token, email, password):
                    super().__init__(token=token, email=email,
                                     password=password, update_token=True)

                def on_token_reset(token):
                    print('My new token is {}'.format(token))

        Using the event decorator:

        .. code-block:: python3

            @client.event()
            async def on_token_reset(token):
                print('My new token is {}'.format(token))

        :param new_token: :class:`str` The new token
        """
        pass

    def event(self, fctn):
        """A decorator that registers an event.

        The only event at present is :func:`on_token_reset`.

        This could be a coro or regular function.

        Example
        --------

        .. code-block:: python3

            @client.event()
            async def on_token_reset(token):
                print('My new token is {}'.format(token))
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
                asyncio.ensure_future(event(*args, **kwargs), loop=self.loop)
            else:
                event(*args, **kwargs)

    def _add_cache(self):
        self._search_clans = {}
        self._war_clans = {}

        self._search_players = {}
        self._war_players = {}

        self._current_wars = {}
        self._war_logs = {}

        self._league_groups = {}
        self._league_wars = {}

        self._locations = {}

        self._leagues = {}
        self._seasons = {}

    def _add_search_clan(self, clan):
        self._search_clans[clan.tag] = clan

    def _remove_search_clan(self, clan_tag):
        self._search_clans.pop(clan_tag, None)

    def _add_war_clan(self, clan):
        self._war_clans[clan.tag] = clan

    def _remove_war_clan(self, clan_tag):
        self._war_clans.pop(clan_tag, None)

    def _add_search_player(self, player):
        self._search_players[player.tag] = player

    def _remove_search_player(self, player_tag):
        self._search_players.pop(player_tag, None)

    def _add_war_player(self, player):
        self._war_players[player.tag] = player

    def _remove_war_player(self, player):
        self._war_players.pop(player.tag, None)

    def _add_current_war(self, war):
        try:
            clan_tag = war.clan.tag
        except AttributeError:
            return

        self._current_wars[clan_tag] = war

    def _remove_current_war(self, war):
        try:
            clan_tag = war.clan.tag
        except AttributeError:
            return

        self._current_wars.pop(clan_tag, None)

    def _add_war_log(self, war):
        try:
            if isinstance(war, list):
                clan_tag = war[0].clan.tag
            else:
                clan_tag = war.clan.tag
        except AttributeError:
            return

        try:
            if isinstance(war, list):
                self._war_logs[clan_tag].extend(war)
            else:
                self._war_logs[clan_tag].append(war)
        except KeyError:
            self._war_logs[clan_tag] = [war]

    def _remove_war_logs(self, clan_tag):
        self._war_logs.pop(clan_tag, None)

    def _add_league_group(self, clan_tag, league_group):
        self._league_groups[clan_tag] = league_group

    def _remove_league_group(self, clan_tag):
        self._league_groups.pop(clan_tag, None)

    def _add_league_war(self, war):
        self._league_wars[war.tag] = war

    def _remove_league_war(self, war_tag):
        self._league_wars.pop(war_tag, None)

    def _add_location(self, location):
        self._locations[location.id] = location

    def _remove_location(self, location_id):
        self._locations.pop(location_id, None)

    def _add_league(self, league):
        self._leagues[league.id] = league

    def _remove_league(self, league_id):
        self._leagues.pop(league_id, None)

    def _add_season(self, league_id, season_id, items):
        self._seasons[league_id][season_id] = items

    def _remove_season_player(self, league_id, season_id):
        self._seasons[league_id].pop(season_id, None)

    async def search_clans(self, *, name: str=None, war_frequency: str=None,
                           location_id: int = None, min_members: int=None, max_members: int=None,
                           min_clan_points: int = None, min_clan_level: int=None, limit: int=None,
                           before: int=None, after: int=None
                           ):
        """
        Search all clans by name and/or filtering the results using various criteria.

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

    async def get_clan(self, tag, cache=False, fetch=True, json=False):
        """
        Get information about a single clan by clan tag. Clan tags can be found using clan search operation.

        :param tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`SearchClan` object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`SearchClan` If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._search_clans.get(tag, None)
            if data:
                return check_json(SearchClan, data, json)

            if fetch is False:
                return None

        r = await self.http.get_clan(tag)

        c = SearchClan(data=r)
        self._add_search_clan(c)
        return c

    async def get_members(self, clan_tag, cache=False, fetch=True):
        """
        List clan members

        :param clan_tag: :class:`str` The clan tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned

        :return: :class:`list` of :class:`BasicPlayer`
        """
        if cache:
            c = self._search_clans.get(clan_tag, None)
            if c:
                if not isinstance(c, SearchClan):
                    c = SearchClan(data=c)

                members = c.members
                if members:
                    return members

            if fetch is False:
                return None

        r = await self.http.get_clan(clan_tag)
        self._add_search_clan(r)
        players = list(BasicPlayer(data=n) for n in r.get('members', []))

        return players

    async def get_warlog(self, clan_tag, cache=False, fetch=True, json=False):
        """
        Retrieve clan's clan war log

        :param clan_tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`WarLog` object
                    or json as returned by API

                    Defaults to ``False``.

        :return: :class:`list` of either :class:`WarLog` or :class:`LeagueWarLogEntry`, according to which war it is,
         If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._war_logs.get(clan_tag, None)
            if data:
                return check_json((WarLog, LeagueWarLogEntry), data, json)

            if fetch is False:
                return None

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
            self._add_war_log(wars)

        return wars

    async def get_current_war(self, clan_tag, cache=False, fetch=True, json=False):
        """
        Retrieve information about clan's current clan war

        :param clan_tag: :class:`str` The clan tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`CurrentWar` object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`CurrentWar` If ``json=False``, else :class:`dict`
        """
        if cache:
            wl = self._current_wars.get(clan_tag, None)
            if wl:
                return check_json(CurrentWar, wl, json)

            if fetch is False:
                return None

        r = await self.http.get_clan_current_war(clan_tag)

        if json is False:
            war = CurrentWar(data=r)
        else:
            war = r

        self._add_current_war(war)

        return war

    async def get_league_group(self, clan_tag, cache=False, fetch=True, json=False):
        """Retrieve information about clan's current clan war league group

        :param clan_tag: :class:`str` The tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`LeagueGroup`
                                            object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`LeagueGroup` If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._league_groups.get(clan_tag, None)
            if data:
                return check_json(LeagueGroup, data, json)

            if fetch is False:
                return None

        r = await self.http.get_clan_war_league_group(clan_tag)
        league = LeagueGroup(data=r)
        self._add_league_group(clan_tag, league)

        return league

    async def get_league_war(self, war_tag, cache=False, fetch=True, json=False):
        """
        Retrieve information about a clan war league war

        :param war_tag: :class:`str` The tag of league war to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`LeagueWar` object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`LeagueWar` If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._league_groups.get(war_tag, None)
            if data:
                return check_json(LeagueWar, data, json)

            if fetch is False:
                return None

        r = await self.http.get_cwl_wars(war_tag)
        war = LeagueWar(data=r)
        self._add_league_war(war)

        return war

    # locations
    async def search_locations(self, *, limit: int=10,
                               before: int=None, after: int=None,
                               json=False):
        """
        List all available locations

        :param limit: Optional[:class:`int`] Number of items to fetch. Default is 10
        :param json: Optional[:class:`bool`] Indicates to return a :class:`Location` object or json as returned by API
                    Defaults to ``False``.

        :raise HTTPException: no options were passed

        :return: :class:`list` of all :class:`Location` found is ``json=False`` else :class:`dict`

        """

        data = await self.http.search_locations(limit=limit, before=before, after=after)

        locations = other_check(Location, data, json)

        for n in locations:
            self._add_location(n)

        return locations

    async def get_location(self, location_id, cache=False, fetch=True, json=False):
        """
        Get information about specific location

        :param location_id: :class:`int` The location ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`Location` object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`Location` If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._locations.get(location_id, None)
            if data:
                return check_json(Location, data, json)

            if fetch is False:
                return None

        r = await self.http.get_location(location_id)
        location = Location(data=r)
        self._add_location(location)

        return location

    async def get_location_clan(self, location_id, *, limit: int=None,
                                before: int=None, after: int=None, json=False):
        """
        Get clan rankings for a specific location


        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :param json: Optional[:class:`bool`] Indicates to return a :class:`Clan` object or json as returned by API
                    Defaults to ``False``.
        :return: :class:`Clan` If ``json=False``, else :class:`dict`
        """

        r = await self.http.get_location_clans(location_id, limit=limit, before=before, after=after)

        return other_check(Clan, r, json)

    async def get_location_players(self, location_id, *, limit: int=None,
                                   before: int=None, after: int=None, json=False):
        """
        Get player rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :param json: Optional[:class:`bool`] Indicates to return a :class:`Player` object or json as returned by API
                    Defaults to ``False``.
        :return: :class:`Player` If ``json=False``, else :class:`dict`
        """
        r = await self.http.get_location_players(location_id, limit=limit, before=before, after=after)

        return other_check(Player, r, json)

    async def get_location_clans_versus(self, location_id, *, limit: int=None,
                                        before: int=None, after: int=None, json=False):
        """
        Get clan versus rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :param json: Optional[:class:`bool`] Indicates to return a :class:`Clan` object or json as returned by API
                    Defaults to ``False``.
        :return: :class:`Clan` If ``json=False``, else :class:`dict`
        """
        r = await self.http.get_location_clans_versus(location_id, limit=limit, before=before, after=after)
        return other_check(Clan, r, json)

    async def get_location_players_versus(self, location_id, *, limit: int = None,
                                          before: int = None, after: int = None, json=False):
        """
        Get player versus rankings for a specific location

        :param location_id: :class:`int` The location ID to search
        :param limit: :class:`int` The number of results to fetch

        :param json: Optional[:class:`bool`] Indicates to return a :class:`Player` object or json as returned by API
                    Defaults to ``False``.
        :return: :class:`Player` If ``json=False``, else :class:`dict`
        """
        r = await self.http.get_location_players_versus(location_id, limit=limit, before=before, after=after)
        return other_check(Player, r, json)

    # leagues

    async def search_leagues(self, *, limit: int=None, before: int=None, after: int=None, json=False):
        """
        Get list of leagues.

        :param limit: Optional[:class:`int`] Number of items to fetch. Default is 10
        :param json: Optional[:class:`bool`] Indicates to return :class:`League` objects or json as returned by API
                    Defaults to ``False``.

        :raise HTTPException: no options were passed

        :return: :class:`list` of all :class:`League` found is ``json=False`` else :class:`dict`

        """

        r = await self.http.search_leagues(limit=limit, before=before, after=after)
        leagues = other_check(League, r, json)

        for n in leagues:
            self._add_league(n)

        return leagues

    async def get_league(self, league_id, cache=False, fetch=True, json=False):
        """
        Get league information

        :param league_id: :class:`str` The ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`League` object or json as returned by API
                    Defaults to ``False``.

        :return: :class:`League` If ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._leagues.get(league_id, None)
            if data:
                return check_json(League, data, json)
            if fetch is False:
                return None

        r = await self.http.get_league(league_id)
        league = League(data=r)
        self._add_league(league)

        return league

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

    async def get_season_rankings(self, league_id, season_id, cache=False, fetch=True, json=False):
        """Get league season rankings.
        Note that league season information is available only for Legend League.

        :param league_id: :class:`str` The league ID to search for
        :param season_id: :class:`str` The season ID to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`LeagueRankedPlayer` object
                                            or json as returned by API
                    Defaults to ``False``.

        :return: :class:`list` of :class:`LeagueRankedPlayer` if ``json=False``, else :class:`dict`
        """
        if cache:
            try:
                data = self._seasons[league_id][season_id]
                return check_json(LeagueRankedPlayer, data, json)

            except KeyError:
                pass

            if fetch is False:
                return None

        r = await self.http.get_league_season_info(league_id, season_id)
        players = list(LeagueRankedPlayer(data=n) for n in r.get('items', []))

        self._add_season(league_id, season_id, players)

        return players

    # players
    async def get_player(self, player_tag, cache=False, fetch=True, json=False):
        """Get information about a single player by player tag.
        Player tags can be found either in game or by from clan member lists.

        :param player_tag: :class:`str` The player tag to search for
        :param cache: Optional[:class:`bool`] Indicates whether to search the cache before making an HTTP request
        :param fetch: Optional[:class:`bool`] Indicates whether an HTTP call should be made if cache is empty.
                        Defaults to ``True``. If this is ``False`` and item in cache was not found,
                        ``None`` will be returned
        :param json: Optional[:class:`bool`] Indicates to return a :class:`LeaguePlayer` object
                                            or json as returned by API
                    Defaults to ``False``.

        :return: :class:`SearchPlayer` if ``json=False``, else :class:`dict`
        """
        if cache:
            data = self._search_players.get(player_tag, None)
            if data:
                return check_json(SearchPlayer, data, json)

            if fetch is False:
                return None

        r = await self.http.get_player(player_tag)
        p = SearchPlayer(data=r)
        self._add_search_player(p)

        return p

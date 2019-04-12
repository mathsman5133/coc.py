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


import json
import logging
import aiohttp
import asyncio

from urllib.parse import urlencode

from .errors import HTTPException, Maitenance, NotFound, InvalidArgument, InvalidToken, Forbidden

log = logging.getLogger(__name__)


async def json_or_text(response):
    try:
        ret = await response.json()
    except:
        ret = await response.text(encoding='utf-8')

    return ret


class Route:
    BASE = 'https://api.clashofclans.com/v1'
    API_PAGE_BASE = 'https://developer.clashofclans.com/api'

    def __init__(self, method, path, kwargs: dict=None, api_page=False):
        if '#' in path:
            path = path.replace('#', '%23')

        self.method = method
        self.path = path
        url = (self.API_PAGE_BASE + self.path if api_page else self.BASE + self.path)

        if kwargs:
            self.url = '{}?{}'.format(url, urlencode({k: v for k, v in kwargs.items() if v is not None}))
        else:
            self.url = url


class HTTPClient:
    def __init__(self, token, loop=None, *, email, password, update_tokens=False):
        self.token = token
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.__session = None
        self.email = email
        self.password = password
        self.update_tokens = update_tokens
        self.loop.run_until_complete(self.login())

    async def login(self):
        self.__session = aiohttp.ClientSession(loop=self.loop)

        # try:
        #     data = await self.request(Route('GET', '', {}))
        # except HTTPException as e:
        #     if e.response.status == 403:
        #         raise InvalidToken(e, 'invalid token has been passed') from e
        #     raise
        # return self

    async def close(self):
        if self.__session:
            await self.__session.close()

    async def request(self, route, **kwargs):
        method = route.method
        url = route.url

        headers = {
            "Accept": "application/json",
            "authorization": "Bearer {}".format(self.token),
        }

        if 'headers' in kwargs:
            kwargs['headers'].update(headers)
        else:
            kwargs['headers'] = headers

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'

        async with self.__session.request(method, url, **kwargs) as r:
            log.debug('%s (%s) has returned %s', url, method, r.status)
            data = await json_or_text(r)

            if 200 <= r.status < 300:
                log.debug('%s has received %s', url, data)
                return data

            if r.status == 400:
                raise InvalidArgument(r, data)
            if r.status == 403:
                if r.reason == 'accessDenied.invalidIp':
                    if self.update_tokens:
                        log.info('Resetting Clash of Clans token')
                        await self.reset_token()
                        return await self.request(route, **kwargs)
                    log.info('detected invalid token, however client requested not to reset.')
                    raise InvalidToken(r, data)

                raise Forbidden(r, data)

            if r.status == 404:
                raise NotFound(r, data)

            if r.status == 503:
                raise Maitenance(r, data)
            else:
                raise HTTPException(r, data)

    async def reset_token(self):
        async with self.__session.request('GET', 'http://ip.42.pl/short') as r:
            log.debug('%s (%s) has returned %s', 'http://ip.42.pl/short', 'GET', r.status)

            ip = await r.text()

            log.debug('%s has received %s', 'http://ip.42.pl/short', ip)

        token_name = 'aio-coc created token'
        token_description = 'learn more about this project at: '

        whitelisted_ips = [ip]

        response_dict, session = await self.login_to_site(self.email, self.password)

        game_api_token = response_dict['temporaryAPIToken']
        game_api_url = response_dict['swaggerUrl']

        cookies = f'session={session};game-api-url={game_api_url};game-api-token={game_api_token}'

        current_tokens = await self.find_site_tokens(cookies)

        for token in current_tokens['keys']:

            if ip in token['cidrRanges']:
                self.token = token['key']
                return token['key']

            else:
                # otherwise if its an outdated IP adress we don't need it anymore,
                # so lets delete it to not clog them up
                # and to prevent hitting the 10 token limit
                token_id = token['id']
                await self.delete_token(cookies, token_id)

        response = await self.create_token(cookies, token_name, token_description, whitelisted_ips)

        clean_token = response['key']['key']

        self.token = clean_token
        return clean_token

    # clans

    def search_clans(self, **kwargs):
        return self.request(Route('GET', '/clans', kwargs))

    def get_clan(self, tag):
        return self.request(Route('GET', '/clans/{}'.format(tag), {}))

    def get_clan_members(self, tag):
        return self.request(Route('GET', '/clans/{}/members'.format(tag), {}))

    def get_clan_warlog(self, tag):
        return self.request(Route('GET', '/clans/{}/warlog'.format(tag), {}))

    def get_clan_current_war(self, tag):
        return self.request(Route('GET', '/clans/{}/currentwar'.format(tag), {}))

    def get_clan_war_league_group(self, tag):
        return self.request(Route('GET', '/clans/{}/currentwar/leaguegroup'.format(tag), {}))

    def get_cwl_wars(self, war_tag):
        return self.request(Route('GET', '/clanwarleagues/wars/'.format(war_tag), {}))

    # locations

    def search_locations(self, **kwargs):
        return self.request(Route('GET', '/locations', kwargs))

    def get_location(self, location_id):
        return self.request(Route('GET', '/locations/{}'.format(location_id), {}))

    def get_location_clans(self, location_id, **kwargs):
        return self.request(Route('GET', '/locations/{}/rankings/clans'.format(location_id), kwargs))

    def get_location_players(self, location_id, **kwargs):
        return self.request(Route('GET', '/locations/{}/rankings/players'.format(location_id), kwargs))

    def get_location_clans_versus(self, location_id, **kwargs):
        return self.request(Route('GET', '/locations/{}/rankings/clans-versus'.format(location_id), kwargs))

    def get_location_players_versus(self, location_id, **kwargs):
        return self.request(Route('GET', '/locations/{}/rankings/players-versus'.format(location_id), kwargs))

    # leagues

    def search_leagues(self, **kwargs):
        return self.request(Route('GET', '/leagues', kwargs))

    def get_league(self, league_id):
        return self.request(Route('GET', '/leagues/{}'.format(league_id), {}))

    def get_league_seasons(self, league_id, **kwargs):
        return self.request(Route('GET', '/leagues/{}/seasons'.format(league_id), kwargs))

    def get_league_season_info(self, league_id, season_id, **kwargs):
        return self.request(Route('GET', '/leagues/{}/seasons/{}'.format(league_id, season_id), kwargs))

    # players

    def get_player(self, player_tag):
        return self.request(Route('GET', '/players/{}'.format(player_tag), {}))

    # token updating management

    async def login_to_site(self, email, password):
        login_data = {
            'email': email,
            'password': password
                      }
        headers = {
            'content-type': 'application/json'
        }
        async with self.__session.post('https://developer.clashofclans.com/api/login',
                                       json=login_data, headers=headers) as sess:
            response_dict = await sess.json()
            log.debug('%s has received %s', 'https://developer.clashofclans.com/api/login',
                      response_dict)

            session = sess.cookies.get('session').value

        return response_dict, session

    async def find_site_tokens(self, cookies):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }
        async with self.__session.post('https://developer.clashofclans.com/api/apikey/list',
                                       data=json.dumps({}), headers=headers) as sess:
            existing_tokens_dict = await sess.json()
            log.debug('%s has received %s', 'https://developer.clashofclans.com/api/apikey/list',
                      existing_tokens_dict)

        return existing_tokens_dict

    async def create_token(self, cookies, token_name, token_description, cidr_ranges):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }

        data = {
            "name": token_name,
            "description": token_description,
            "cidrRanges": cidr_ranges
        }

        r = await self.request(Route('POST', '/apikey/create', api_page=True), json=data, headers=headers)
        return r['key']['key']

    def delete_token(self, cookies, token_id):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }

        data = {
            "id": token_id
        }

        return self.request(Route('POST', '/apikey/revoke', api_page=True), json=data, headers=headers)

    async def get_data_from_url(self, url):
        async with self.__session.get(url) as r:
            if r.status == 200:
                return await r.read()
            elif r.status == 404:
                raise NotFound(r, 'image not found')
            else:
                raise HTTPException(r, 'failed to get image')


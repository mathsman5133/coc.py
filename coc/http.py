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
from itertools import cycle
from datetime import datetime
from .errors import HTTPException, Maitenance, NotFound, InvalidArgument, Forbidden

log = logging.getLogger(__name__)
KEY_MINIMUM, KEY_MAXIMUM = 1, 10


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
    def __init__(self, client, loop, email, password,
                 key_names, key_count):
        self.client = client
        self.loop = loop
        self.email = email
        self.password = password
        self.key_names = key_names
        self.key_count = key_count

        loop.run_until_complete(self.get_keys())

    async def get_keys(self):
        self.__session = aiohttp.ClientSession(loop=self.loop)
        key_count = self.key_count
        ip = await self.get_ip()
        response_dict, session = await self.login_to_site(self.email, self.password)
        cookies = self.create_cookies(response_dict, session)
        current_keys = (await self.find_site_keys(cookies))['keys']
        self._keys = [key['key'] for key in current_keys if key['name'] == self.key_names]
        available_keys = KEY_MAXIMUM - len(current_keys)

        if len(self._keys) <= key_count:
            keys_needed = key_count - len(self._keys)
            if available_keys >= keys_needed:
                for _ in range(keys_needed):
                    key_description = "Created on {}".format(datetime.now().strftime('%c'))
                    self._keys.append(await self.create_key(
                        cookies,self.key_names, key_description, [ip]))
            else:
                await self.close()
                raise RuntimeError(("There are {} API keys already created and {} match \"{}\" out of a max of "
                                    "{} please goto {} and delete unused keys or rename to \"{}\".").format(
                    len(current_keys), len(self._keys),
                    self.key_names, KEY_MAXIMUM,
                    'https://developer.clashofclans.com',
                    self.key_names))

        self.keys = cycle(self._keys)

    async def close(self):
        if self.__session:
            await self.__session.close()

    async def request(self, route, **kwargs):
        key = next(self.keys)
        method = route.method
        url = route.url

        if 'headers' not in kwargs:
            headers = {
                "Accept": "application/json",
                "authorization": "Bearer {}".format(key),
            }
            kwargs['headers'] = headers

        if 'json' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'

        async with self.__session.request(method, url, **kwargs) as r:
            log.debug('%s (%s) has returned %s', url, method, r.status)
            data = await json_or_text(r)

            if 200 <= r.status < 300:
                log.debug('%s has received %s', url, data)
                return data

            if r.status == 400:
                raise InvalidArgument(r, data)

            if r.status == 403:
                if data.get('reason') in ['accessDenied.invalidIp']:
                    log.info('Resetting Clash of Clans key')
                    await self.reset_key(key)
                    return await self.request(route, **kwargs)

                raise Forbidden(r, data)

            if r.status == 404:
                raise NotFound(r, data)
            if r.status == 429:
                # TODO: Implement ratelimits
                # This could look like an optional user set ratelimit (default 10req/sec)
                # or some other method you think up.
                # for now divert to HTTPException
                raise HTTPException(r, data)

            if r.status == 503:
                raise Maitenance(r, data)
            else:
                raise HTTPException(r, data)

    async def get_ip(self):
        async with self.__session.request('GET', 'http://ip.42.pl/short') as r:
            log.debug('%s (%s) has returned %s', 'http://ip.42.pl/short', 'GET', r.status)
            ip = await r.text()
            log.debug('%s has received %s', 'http://ip.42.pl/short', ip)
        return ip

    @staticmethod
    def create_cookies(response_dict, session):
        return "session={};game-api-url={};game-api-token={}".format(
            session,
            response_dict['swaggerUrl'],
            response_dict['temporaryAPIToken']
        )

    async def reset_key(self, key):
        ip = await self.get_ip()
        # TODO: Distinguish/recognise by key name rather than current ip for running clients on multiple IPs
        # should probably put something else in here
        # to distinguish each key like a date
        key_name = 'coc.py created key'
        # Also, probably fix this as well
        key_description = 'learn more about this project at: https://github.com/mathsman5133/coc.py'
        whitelisted_ips = [ip]

        response_dict, session = await self.login_to_site(self.email, self.password)
        cookies = self.create_cookies(response_dict, session)

        existing_keys = (await self.find_site_keys(cookies))['keys']
        key_id = [t['id'] for t in existing_keys if t['key'] == key]

        await self.delete_key(cookies, key_id)

        new_key = await self.create_key(cookies, key_name, key_description, whitelisted_ips)

        # this is to prevent reusing an already used keys.
        # All it does is move the current key to the front,
        # by moving any already used ones to the end so
        # we keep the original key order moving forward.
        keys = self._keys
        key_index = keys.index(key)
        self._keys = keys[key_index:] + keys[:key_index]

        # now we can set the new key which is the first
        # one in self._keys, then start the cycle over.
        self._keys[0] = new_key
        self.keys = cycle(self.keys)
        self.client.dispatch('key_reset', new_key)

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

    # key updating management

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

    async def find_site_keys(self, cookies):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }
        async with self.__session.post('https://developer.clashofclans.com/api/apikey/list',
                                       data=json.dumps({}), headers=headers) as sess:
            existing_keys_dict = await sess.json()
            log.debug('%s has received %s', 'https://developer.clashofclans.com/api/apikey/list',
                      existing_keys_dict)

        return existing_keys_dict

    async def create_key(self, cookies, key_name, key_description, cidr_ranges):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }

        data = {
            "name": key_name,
            "description": key_description,
            "cidrRanges": cidr_ranges
        }

        r = await self.request(Route('POST', '/apikey/create', api_page=True), json=data, headers=headers)
        return r['key']['key']

    def delete_key(self, cookies, key_id):
        headers = {
            "cookie": cookies,
            "content-type": "application/json"
        }
        log.critical(headers)

        data = {
            "id": key_id
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

"""An extension that helps interact with the FullWar API."""

import asyncio
import base64
import logging
import json

from collections import namedtuple
from datetime import datetime
from typing import Generator, List, Optional, Union

import aiohttp

import coc
from ...http import json_or_text
from ...utils import correct_tag
from ...wars import ClanWar

LOG = logging.getLogger(__name__)

FWAccessToken = namedtuple("FWAccessToken", ["token", "expires_at"])


def extract_expiry_from_jwt_token(token: Union[str, bytes]) -> Optional[datetime]:
    if isinstance(token, str):
        token = token.encode("utf-8")
    elif not isinstance(token, bytes):
        # token was wrong somehow
        return None

    try:
        signing, _ = token.rsplit(b".", 1)
        _, payload = signing.split(b".", 1)
    except ValueError:
        return None  # not enough segments

    if len(payload) % 4 > 0:
        payload += b"=" * (4 - len(payload) % 4)

    bytes_payload = base64.urlsafe_b64decode(payload)
    dict_payload = json.loads(bytes_payload)
    try:
        expiry = dict_payload["exp"]
        return datetime.fromtimestamp(expiry)
    except KeyError:
        return None


async def login(username: str, password: str, coc_client: Union[coc.Client, coc.EventsClient]) -> "FullWarClient":
    """Eases logging into the API client.

    For more information on this project, please join the discord server - <discord.gg/Eaja7gJ>

    You must have your username and password as given on the server.
    If unsure as to what this means, please reach out to an admin.

    Parameters
    -----------
    username : str
        Your username as given on the discord server.
    password : str
        Your password as given on the discord server
    coc_client : Union[coc.Client, coc.EventsClient]
        A coc_client to grap the loop from and create the response objects with
    """
    if not isinstance(username, str) or not isinstance(password, str):
        raise TypeError("username and password must both be a string")
    if not username or not password:
        raise ValueError("username or password must not be an empty string.")

    return FullWarClient(username, password, coc_client)


class FullWarClient:
    """An extension that helps interact with the Full War API.

    For more information on this project, please join the discord server - <discord.gg/Eaja7gJ>

    You must have your username and password as given on the server.
    If unsure as to what this means, please reach out to an admin.

    Parameters
    -----------
    username : str
        Your username as given on the discord server.
    password : str
        Your password as given on the discord server
    coc_client: Union[coc.Client, coc.EventClient]
        Client to use
    loop : Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for HTTP requests.
        An :func:`asyncio.get_event_loop()` will be used if ``None`` is passed

    """

    BASE_URL = "https://fw-api.teamutils.com"

    __slots__ = ("username", "password", "coc_client", "loop", "key", "http_session")

    def __init__(self, username: str, password: str, coc_client: Union[coc.Client, coc.EventsClient],
                 loop: asyncio.AbstractEventLoop = None):
        self.username = username
        self.password = password
        self.coc_client = coc_client

        self.loop = coc_client.loop or asyncio.get_event_loop()
        self.key = None  # set in get_key()

        self.http_session = aiohttp.ClientSession(loop=self.loop)

    async def close(self):
        """Close the client session established"""
        await self.http_session.close()

    async def _request(self, method, url, *, token_request: bool = False, **kwargs):
        url = self.BASE_URL + url

        if not token_request:
            key = await self._get_key()

            headers = {"authorization": "Bearer {}".format(key)}
            kwargs["headers"] = headers

        async with self.http_session.request(method, url, **kwargs) as response:
            LOG.debug("%s (%s) has returned %s", url, method, response.status)
            data = await json_or_text(response)
            LOG.debug(data)

            if 200 <= response.status < 300:
                LOG.debug("%s has received %s", url, data)
                return data

            if response.status == 401:
                await self._refresh_key()
                return await self._request(method, url, **kwargs)

    async def _get_key(self):
        if not self.key or (self.key.expires_at and self.key.expires_at < datetime.utcnow()):
            await self._refresh_key()

        return self.key.token

    async def _refresh_key(self):
        data = {
            "username": self.username,
            "password": self.password,
        }

        payload = await self._request("POST", "/login", token_request=True, json=data)
        self.key = FWAccessToken(payload["access_token"], extract_expiry_from_jwt_token(payload["access_token"]))

    async def war_result(self, clan_tag: str, preparation_start: int = 0) -> Optional[ClanWar]:
        """Get a stored war result.

        Parameters
        ----------
        clan_tag: str
            The clan tag to find war result for.
        preparation_start: int
            Preparation start of a specific war result to find.

        Returns
        --------
        Optional[:class:`ClanWar`]
            War result, or ``None`` if no war found.
        """
        data = await self._request("GET",
                                   f"/war_result?clan_tag={correct_tag(clan_tag, '%23')}"
                                   f"&prep_start={str(preparation_start)}")
        try:
            return ClanWar(data=data["response"], client=self.coc_client, clan_tag=coc.utils.correct_tag(clan_tag))
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    async def war_result_log(self, clan_tag: str) -> Optional[Generator[ClanWar, None, None]]:
        """Get all stored war results for a clan.

        Parameters
        ----------
        clan_tag: str
            The clan tag to find war result for.

        Returns
        --------
        Optional[Generator[:class:`ClanWar`]]
            Generator of war results, or ``None`` if no wars found.
        """
        data = await self._request("GET",
                                   f"/war_result_log?clan_tag={correct_tag(clan_tag, '%23')}")
        try:
            responses = data["log"]
            return (ClanWar(data=response["response"], client=self.coc_client,
                            clan_tag=coc.utils.correct_tag(clan_tag)) for response in responses)
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    async def register_war(self, clan_tag: str, preparation_start: int = 0):
        """Registers a war.

        Parameters
        ----------
        clan_tag : str
            The clan to register a war for
        preparation_start: int
            Preparation time of the war.
        """
        return await self._request("POST",
                                   f"/register_war?clan_tag={correct_tag(clan_tag, '%23')}"
                                   f"&prep_start={str(preparation_start)}")


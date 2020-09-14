"""An extension that helps interact with the Clash of Clans Discord Junkies' Discord Links API."""

import asyncio
import logging
import typing

from collections import namedtuple
from datetime import datetime, timedelta

import aiohttp

from coc.http import json_or_text
from coc.utils import correct_tag

LOG = logging.getLogger(__name__)

AccessToken = namedtuple("AccessToken", ["token", "expires_at"])


def login(username: str, password: str, loop: asyncio.AbstractEventLoop = None) -> "DiscordLinkClient":
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
    loop : Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for HTTP requests.
        An :func:`asyncio.get_event_loop()` will be used if ``None`` is passed
    """
    if not isinstance(username, str) or not isinstance(password, str):
        raise TypeError("username and password must both be a string")
    if not username or not password:
        raise ValueError("username or password must not be an empty string.")
    if loop and not isinstance(loop, asyncio.AbstractEventLoop):
        raise TypeError("loop must be of type asyncio.AbstractEventLoop, or None.")

    return DiscordLinkClient(username, password, loop)


class DiscordLinkClient:
    """An extension that helps interact with the Clash of Clans Discord Junkies' Discord Links API.

    For more information on this project, please join the discord server - <discord.gg/Eaja7gJ>

    You must have your username and password as given on the server.
    If unsure as to what this means, please reach out to an admin.

    Parameters
    -----------
    username : str
        Your username as given on the discord server.
    password : str
        Your password as given on the discord server

    loop : Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for HTTP requests.
        An :func:`asyncio.get_event_loop()` will be used if ``None`` is passed

    """

    BASE_URL = "https://api.amazingspinach.com"

    __slots__ = ("username", "password", "loop", "key", "http_session")

    def __init__(self, username: str, password: str, loop: asyncio.AbstractEventLoop = None):
        self.username = username
        self.password = password

        self.loop = loop or asyncio.get_event_loop()
        self.key = None  # set in get_key()

        self.http_session = aiohttp.ClientSession(loop=self.loop)

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
        if not self.key or self.key.expires_at < datetime.utcnow():
            await self._refresh_key()

        return self.key.token

    async def _refresh_key(self):
        data = {
            "username": self.username,
            "password": self.password,
        }

        key = await self._request("POST", "/login", token_request=True, json=data)

        self.key = AccessToken(key["token"], datetime.utcnow() + timedelta(hours=1, minutes=59))

    async def get_discord_link(self, player_tag: str) -> typing.Optional[int]:
        """Get a linked discord ID of a player tag.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag: str
            The player tag to search for.

        Returns
        --------
        Optional[:class:`int`]
            The discord ID linked to the player, or ``None`` if no link found.
        """
        data = await self._request("GET", "/links/{}".format(correct_tag(player_tag)))
        return data and data.get("discordId", None)

    async def get_discord_links(
        self, player_tags: typing.Iterable
    ) -> typing.List[typing.Tuple[str, typing.Optional[str]]]:
        """Get linked discord IDs for an iterable of player tags.
        Player tags can be found either in game or by from clan member lists.

        This is the recommended method to use when fetching links for multiple tags as it uses a different endpoint.

        Parameters
        ----------
        player_tags : :class:`typing.Iterable` of :class:`str`
            The player tags to search for.

        Returns
        --------
        List[:class:`str`:, Optional[:class:`int`]]
            A list of player_tag, discord_id tuple matches. Discord ID will be ``None`` if not found.

        Example
        --------

        .. code-block:: python3

            tags = [...]
            links = await client.get_discord_links(tags)

            for player_tag, discord_id in links:
                print(player_tag, discord_id)

        """
        tags = list(player_tags)
        data = await self._request("POST", "/links/batch", json=tags)
        if not data:
            return []

        return [(n.get("playerTags", [""])[0], n.get("discordId", None)) for n in data]

    async def get_discord_linked_players(self, discord_id: int) -> typing.List[str]:
        """Get a list of player tags linked to a discord ID.

        Parameters
        ----------
        discord_id: int
            The discord ID to search for.

        Returns
        --------
        List[:class:`str`]
         A list of player tags attached to the discord ID. If no links found, this will be an empty list.
        """
        data = await self._request("GET", "/links/{}".format(discord_id))
        if not data:
            return []

        return [item["playerTag"] for item in data]

    async def get_batch_discord_linked_players(
        self, discord_ids: typing.Iterable
    ) -> typing.List[typing.Tuple[int, typing.Tuple[str]]]:
        """Get a linked discord ID of a player tag.

        This is the recommended method to use when fetching links for multiple IDs as it uses a different endpoint.

        Parameters
        -----------
        discord_ids: :class:`typing.Iterable` of :class:`int`
            The discord IDs to search for.

        Returns
        --------
        List[Tuple[:class:`int`, Tuple[:class:`str`]]]
            A list containing (discord_id, (tuple of tags)) matches.

        Example
        -------

        .. code-block:: python3

            discord_ids = [...]
            links = await client.get_batch_discord_linked_players(discord_ids)

            for discord_id, player_tags in links:
                # discord_id is an int, player_tags is a tuple of tags. Will be empty if no matches found.
                print(discord_id, ', '.join(player_tags))
        """
        data = await self._request("POST", "/links/batch", json=[str(n) for n in discord_ids])
        if not data:
            return []

        return [(n["discordId"], tuple(n["playerTags"])) for n in data]

    async def add_discord_link(self, player_tag: str, discord_id: int):
        """Creates a link between a player tag and a discord ID for the shared junkies database.
        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to add the link to.
        discord_id: int
            The discord ID to add the link to.
        """
        data = {"playerTag": correct_tag(player_tag, prefix=""), "discordId": str(discord_id)}
        return await self._request("POST", "/links", json=data)

    async def update_discord_link(self, player_tag: str, discord_id: int):
        """Updates the discord ID for a link between a player tag and a discord ID for the shared junkies database.

        Player tags can be found either in game or by from clan member lists.

        Parameters
        ----------
        player_tag : str
            The player tag to add the link to.
        discord_id: int
            The discord ID to add the link to.
        """
        data = {"playerTag": correct_tag(player_tag, prefix=""), "discordId": str(discord_id)}
        return await self._request("PUT", "/links", json=data)

    async def delete_discord_link(self, player_tag: str):
        """Deletes a link between a player tag and a discord ID for the shared junkies database.

       Player tags can be found either in game or by from clan member lists.

       Parameters
       ----------
       player_tag : str
           The player tag to add the link to.
       """
        return await self._request("POST", "/links/{}".format(correct_tag(player_tag, prefix="")))

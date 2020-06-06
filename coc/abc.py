from abc import ABC

from .miscmodels import try_enum, Badge
from .iterators import PlayerIterator


class BaseClan(ABC):
    """An ABC that implements some common operations on clans, regardless of type.

    Attributes
    -----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    """

    __slots__ = ("tag", "name", "_client", "badge", "_member_tags", "level", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % self.__class__.__name__, self.tag, self.name

    def __eq__(self, other):
        return isinstance(self, other.__class__) and self.tag == other.tag

    def __init__(self, *, data, client, **kwargs):
        self._client = client

        self._response_retry = data.get("_response_retry")
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.badge = try_enum(Badge, data=data.get("badgeUrls"), client=self._client)
        self.level = data.get("clanLevel")

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the clan in-game"""
        return "https://link.clashofclans.com/en?action=OpenClanProfile&tag=%23{}".format(self.tag.strip("#"))

    async def get_clan_details(self):
        return await self._client.get_clan(self.tag)

    def get_detailed_members(self, cache: bool = False):
        """Get detailed player information for every player in the clan.
        This will return an AsyncIterator of :class:`SearchPlayer`.

        Example
        --------

        .. code-block:: python3

            clan = await client.get_clan('tag')

            async for player in clan.get_detailed_members(cache=True):
                print(player.name)

        Parameters
        -----------
        cache: Optional[:class:`bool`]: Whether to use the bot's cache before making a HTTP request.
                                        If a player is not found, only then make a request.
                                        If using the events client, it is suggested that this be ``True``.
                                        Defaults to ``False``.

        Returns
        -------
        AsyncIterator of :class:`SearchPlayer`: the clan members.
        """
        if not self._member_tags:
            return NotImplemented

        return PlayerIterator(self._client, self._member_tags, cache)


class BasePlayer(ABC):
    """An ABC that implements some common operations on players, regardless of type.

    Attributes
    -----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    """

    __slots__ = ("tag", "name", "_client", "_response_retry")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s tag=%s name=%s>" % (self.__class__.__name__, self.tag, self.name,)

    def __init__(self, *, data, client, **kwargs):
        self._client = client
        self._response_retry = data.get("_response_retry")

        self.tag = data.get("tag")
        self.name = data.get("name")

    @property
    def share_link(self):
        """:class:`str` - A formatted link to open the player in-game"""
        return "https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{}".format(self.tag.strip("#"))

    async def get_player_details(self):
        return await self._client.get_player(self.tag)

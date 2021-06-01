"""
MIT License

Copyright (c) 2019-2020 mathsman5133

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
import typing


from .players import ClanMember
from .miscmodels import try_enum, ChatLanguage, Location, Label, WarLeague
from .utils import get, cached_property, correct_tag
from .abc import BaseClan


class RankedClan(BaseClan):
    """Represents the clan object returned by leader-board rankings.

    Attributes
    ----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    location: :class:`Location`
        The clan's location.
    member_count: :class:`int`
        The number of members in the clan.
    points: :class:`int`
        The clan's trophy-count. If retrieving info for versus leader-boards, this will be ``None``.
    versus_points: :class:`int`
        The clan's versus trophy count. If retrieving info for regular leader boards, this will be ``None``.
    rank: :class:`int`
        The clan's rank in the leader board.
    previous_rank: :class:`int`
        The clan's rank in the previous season's leaderboard.
    """

    __slots__ = (
        "location",
        "member_count",
        "points",
        "versus_points",
        "rank",
        "previous_rank",
    )

    def __init__(self, *, data, client, **_):
        super().__init__(data=data, client=client)
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.points: int = data_get("clanPoints")
        self.versus_points: int = data_get("clanVersusPoints")
        self.member_count: int = data_get("members")
        self.location = try_enum(Location, data=data_get("location"))
        self.rank: int = data_get("rank")
        self.previous_rank: int = data_get("previousRank")


class Clan(BaseClan):
    """Represents a Clash of Clans clan.

    Attributes
    ----------
    tag: :class:`str`
        The clan's tag
    name: :class:`str`
        The clan's name
    badge: :class:`Badge`
        The clan's badge
    level: :class:`int`
        The clan's level.
    type: :class:`str`
        The clan's type for accepting members.
        This could be ``open``, ``inviteOnly`` or ``closed``.
    description: :class:`str`
        The clan's public description.
    location: :class:`Location`
        The clan's location.
    points: :class:`int`
        The clan's trophy count. This is calculated according to members' trophy counts.
    versus_points: :class:`int`
        The clan's versus trophy count. This is calculated according to members' versus trophy counts.
    required_trophies: :class:`int`
        The minimum trophies required to apply to this clan.
    war_frequency: :class:`str`
        The frequency for when this clan goes to war.
        For example, this could be ``always``.
    war_win_streak: :class:`int`
        The clan's current war winning streak.
    war_wins: :class:`int`
        The number of wars the clan has won.
    war_ties: :class:`int`
        The number of wars the clan has tied.
    war_losses: :class:`int`
        The number of wars the clan has lost.
    public_war_log: :class:`bool`
        Indicates if the clan has a public war log.
        If this is ``False``, operations to find the clan's current war may raise :exc:`PrivateWarLog`.
    member_count: :class:`int`
        The number of members in the clan.
    label_cls: :class:`coc.Label`
        The type which the labels found in :attr:`Clan.labels` will be of.
        Ensure any overriding of this inherits from :class:`coc.Label`.
    member_cls: :class:`coc.ClanMember`
        The type which the members found in :attr:`Clan.members` will be of.
        Ensure any overriding of this inherits from :class:`coc.ClanMember`.
    war_league: :class:`coc.WarLeague`
        The clan's CWL league.
    """

    __slots__ = (
        "type",
        "description",
        "location",
        "points",
        "versus_points",
        "required_trophies",
        "war_frequency",
        "war_win_streak",
        "war_wins",
        "war_ties",
        "war_losses",
        "public_war_log",
        "member_count",
        "_labels",
        "_members",
        "_client",
        "label_cls",
        "member_cls",
        "war_league",
        "chat_language",

        "_cs_labels",
        "_cs_members",
        "_iter_labels",
        "_iter_members",
    )

    def __init__(self, *, data, client, **_):
        super().__init__(data=data, client=client)
        self.label_cls = Label
        self.member_cls = ClanMember

        self._members = None  # type: typing.Optional[typing.Dict[str, ClanMember]]

        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.points: int = data_get("clanPoints")
        self.versus_points: int = data_get("clanVersusPoints")
        self.member_count: int = data_get("members")
        self.location = try_enum(Location, data=data_get("location"))

        # only available via /clans/{clanTag} or /clans endpoint
        self.type: str = data_get("type")
        self.required_trophies: int = data_get("requiredTrophies")
        self.war_frequency: str = data_get("warFrequency")
        self.war_win_streak: int = data_get("warWinStreak")
        self.war_wins: int = data_get("warWins")
        self.war_ties: int = data_get("warTies")
        self.war_losses: int = data_get("warLosses")
        self.public_war_log: bool = data_get("isWarLogPublic")
        self.description: str = data_get("description")
        self.war_league = try_enum(WarLeague, data=data_get("warLeague"))
        self.chat_language = try_enum(ChatLanguage, data=data_get("chatLanguage"))

        label_cls = self.label_cls
        self._iter_labels = (label_cls(data=ldata, client=self._client) for ldata in data_get("labels", []))

        # update members globally. only available via /clans/{clanTag}
        member_cls = self.member_cls
        self._iter_members = (
            member_cls(data=mdata, client=self._client, clan=self) for mdata in data_get("memberList", [])
        )

    @cached_property("_cs_labels")
    def labels(self) -> typing.List[Label]:
        """List[:class:`Label`]: A :class:`List` of :class:`Label` that the clan has."""
        return list(self._iter_labels)

    @cached_property("_cs_members")
    def members(self) -> typing.List[ClanMember]:
        """List[:class:`ClanMember`]: A list of members that belong to the clan."""
        dict_members = self._members = {m.tag: m for m in self._iter_members}
        return list(dict_members.values())

    def get_member(self, tag: str) -> typing.Optional[ClanMember]:
        """Return a :class:`ClanMember` with the tag provided. Returns ``None`` if not found.

        Example
        --------
        .. code-block:: python3

            clan = await client.get_clan('clan_tag')
            member = clan.get_member('player_tag')

        Returns
        --------
        The member who matches the tag provided: Optional[:class:`ClanMember`]
        """
        tag = correct_tag(tag)
        if not self._members:
            _ = self.members

        try:
            return self._members[tag]
        except KeyError:
            return None

    def get_member_by(self, **attrs) -> typing.Optional[ClanMember]:
        """Returns the first :class:`ClanMember` that meets the attributes passed

        This search implements the :func:`coc.utils.get` function

        Example
        -------
        .. code-block:: python3
            clan = await client.get_clan("#clantag")

            member = clan.get_member_by(name="Joe")
            member = clan.get_member_by(level=125)
            member = clan.get_member_by(role=coc.Role.elder)

        """
        return get(self.members, **attrs)

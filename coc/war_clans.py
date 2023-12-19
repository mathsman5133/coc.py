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

from .abc import BaseClan
from .war_members import ClanWarMember, ClanWarLeagueClanMember
from .utils import cached_property, correct_tag

if typing.TYPE_CHECKING:
    from .war_attack import WarAttack  # noqa


class WarClan(BaseClan):
    """Represents a War Clan that the API returns.

    .. note::

        If this is called via :attr:`ClanWarLog.clan`, then :attr:`WarClan.members`,
        :attr:`WarClan.attacks` and :attr:`WarClan.defenses` will be empty.

        If this is called via :attr:`ClanWarLog.opponent`, then :attr:`WarClan.members`,
        :attr:`WarClan.attacks` and :attr:`WarClan.defenses` will be empty.
        :attr:`WarClan.exp_earned` and :attr:`WarClan.attacks` will be ``None``.

        If this is called via :attr:`ClanWar.clan` or :attr:`ClanWar.opponent` then
        :attr:`WarClan.exp_earned` will be ``None``.

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
    stars:
        :class:`int`: Number of stars by clan this war.
    destruction:
        :class:`float`: Destruction as a percentage.
    exp_earned:
        :class:`int`: Total XP earned by clan this war.
    attacks_used:
        :class:`int`: Total attacks used by clan this war.
    max_stars:
        :class:`int`: Total possible stars achievable.
    total_attacks:
        :class:`int`: Total possible number of attacks usable by clan this war
    member_cls: :class:`coc.ClanMember`
        The type which the members found in :attr:`Clan.members` will be of.
        Ensure any overriding of this inherits from :class:`coc.ClanMember`.
    """

    __slots__ = (
        "destruction",
        "level",
        "attacks_used",
        "stars",
        "exp_earned",
        "max_stars",
        "total_attacks",
        "member_cls",
        "_war",
        "_client",

        "_members",
        "_iter_members",
        "_cs_attacks",
        "_cs_defenses",
        "_cs_members",
    )

    def __init__(self, *, data, client, war, **kwargs):
        self._war = war
        self._members = {}
        self.member_cls = kwargs.pop('member_cls', ClanWarMember)

        super().__init__(data=data, client=client)
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.level: int = data_get("clanLevel")
        self.destruction: float = data_get("destructionPercentage")
        self.exp_earned: int = data_get("expEarned")
        self.attacks_used: int = data_get("attacks")
        self.stars: int = data_get("stars")

        if self._war:
            self.max_stars: int = self._war.team_size * 3
            self.total_attacks: int = self._war.team_size * self._war.attacks_per_member
        else:
            self.max_stars: int = (data_get("teamSize") or 0) * 3
            self.total_attacks: int = (data_get("teamSize") or 0) * 3

        self._iter_members = (
            self.member_cls(data=mdata, client=self._client, war=self._war, clan=self)
            for mdata in data_get("members", [])
        )

    @cached_property("_cs_members")
    def members(self) -> typing.List[ClanWarMember]:
        """List[:class:`ClanWarMember`]: A list of members that are in the war.
        This is sorted by :attr:`ClanWarMember.map_position`
        """
        dict_members = self._members = {m.tag: m for m in sorted(self._iter_members, key=lambda m: m.map_position)}
        return list(dict_members.values())

    @property
    def is_opponent(self) -> bool:
        """:class:`bool`: Indicates whether the clan is the opponent."""
        return self.tag == self._war.opponent.tag

    @cached_property("_cs_attacks")
    def attacks(self) -> typing.List["WarAttack"]:
        """List[:class:`WarAttack`]: Returns all clan member's attacks this
        war. This is sorted by attack order."""
        if not self._war:
            return []

        attacks = []
        for member in self.members:
            attacks.extend(member.attacks)

        return list(sorted(attacks, key=lambda a: a.order, reverse=True))

    @cached_property("_cs_defenses")
    def defenses(self) -> typing.List["WarAttack"]:
        """List[:class:`WarAttack`]: Returns all clan member's defenses
        this war. This is sorted by attack order.

        Equivalent to the other team's ``.attacks`` property.
        """
        other = self._war and self._war.clan if self.is_opponent else self._war.opponent
        return other.attacks if other else []
    
    @property
    def average_attack_duration(self) -> int:
        """:class:`int`: Returns the average duration of all clan member's
        attacks this war."""
        count = len(self.attacks)
        total_duration = sum(attack.duration for attack in self.attacks)
        return int(total_duration/count) if count > 0 else 0

    def get_member(self, tag: str) -> typing.Optional[ClanWarMember]:
        """
        Get a member of the clan for the given tag, or ``None`` if not found.

        Returns
        --------
        ClanWarMember or None
            The clan member who matches the tag.: Optional[:class:`ClanWarMember`]"""

        tag = correct_tag(tag)
        if not self._members:
            _ = self.members

        try:
            return self._members[tag]
        except KeyError:
            return None


class ClanWarLeagueClan(BaseClan):
    """Represents a Clan War League Clan.

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
    """

    __slots__ = BaseClan.__slots__ + ("_cs_members", "_iter_members")

    def __init__(self, *, data, client):
        super().__init__(data=data, client=client)

        self._iter_members = (
            ClanWarLeagueClanMember(data=mdata, client=self._client) for mdata in data.get("members", [])
        )

    @cached_property("_cs_members")
    def members(self) -> typing.List[ClanWarLeagueClanMember]:
        """List[:class:`ClanWarLeagueClanMember`]: A list of players participating in this clan war league season.

        This list is selected when the clan chooses to participate in CWL, and will not change throughout the season.
        It is sometimes referred to as the `master roster`.
        """
        return list(self._iter_members)

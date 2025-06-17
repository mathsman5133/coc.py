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

from .abc import BasePlayer
from .war_attack import WarAttack

if typing.TYPE_CHECKING:
    from .wars import ClanWar
    from .war_clans import WarClan


class ClanWarMember(BasePlayer):
    """Represents a War Member that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    town_hall:
        :class:`int`: The member's townhall level.
    map_position:
        :class:`int`: The member's map position in the war.
    defense_count:
        :class:`int`: The number of times this member has been attacked.
    war:
        :class:`ClanWar`: The current war this member is in.
    clan:
        :class:`WarClan`: The member's clan.
    attack_cls: :class:`coc.WarAttack`
        The type which the attacks in :attr:`ClanWarMember.attacks` will be of.
        Ensure any overriding of this inherits from :class:`coc.WarAttack`.
    """

    __slots__ = (
        "tag",
        "name",
        "town_hall",
        "defense_count",
        "__iter_attacks",
        "_attack_opponents",
        "_best_opponent_attacker",
        "map_position",
        "war",
        "clan",
        "attack_cls",
        "_client",
        "_attacks",
    )

    def __init__(self, *, data, client, war, clan, **kwargs):
        super().__init__(data=data, client=client)
        self._client = client
        self._attacks = []
        self.war = war  # type: ClanWar
        self.clan = clan  # type: WarClan
        self.attack_cls = kwargs.pop('attack_cls', WarAttack)
        self._from_data(data)

    def _from_data(self, data):
        data_get = data.get

        self.name: str = data_get("name")
        self.tag: str = data_get("tag")
        self.town_hall: int = data_get("townhallLevel")
        self.map_position: int = data_get("mapPosition")
        self.defense_count: int = data_get("opponentAttacks")

        self.__iter_attacks = (
            self.attack_cls(data=adata, client=self._client, war=self.war) for adata in data_get("attacks", [])
        )

        self._best_opponent_attacker: str = data_get("bestOpponentAttack", {}).get("attackerTag")

    @property
    def best_opponent_attack(self) -> WarAttack:
        """:class:`WarAttack`: Returns the best opponent attack on this base."""
        return self.war.get_attack(self._best_opponent_attacker, self.tag)

    @property
    def previous_best_opponent_attack(self):
        """:class:`WarAttack`: Returns the previous best opponent attack on this base.

        This is useful for calculating the new stars and/or destruction for new attacks.
        """

        def key(item):
            # 100^3 > 99^2 > 50^2 > 99^1. Smallest/largest values possible.
            return item != self.best_opponent_attack and item.destruction ** item.stars

        # Potential caveat: how does order effect this?
        return max(self.defenses, key=key)

    @property
    def attacks(self) -> typing.List[WarAttack]:
        """List[:class:`WarAttack`]: The member's attacks this war. Could be an empty list."""
        list_attacks = self._attacks
        if list_attacks:
            return list_attacks

        list_attacks = self._attacks = list(self.__iter_attacks)
        return list_attacks

    @property
    def defenses(self) -> typing.List[WarAttack]:
        """List[:class:`WarAttack`]: The member's defenses this war. Could be an empty list."""
        return self.war.get_defenses(self.tag)

    @property
    def is_opponent(self) -> bool:
        """:class:`bool`: Indicates whether the member is from the opponent clan or not."""
        return self.clan and self.war.opponent and self.clan.tag == self.war.opponent.tag or False

    @property
    def star_count(self):
        """:class:`int`: Get the total number of stars the member has gained this war."""
        return sum(attack.stars for attack in self.attacks)


class ClanWarLeagueClanMember(BasePlayer):
    """Represents a clan member who is a part of the Clan War League master roster.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    town_hall: :class:`int`
        The player's town hall level.
    """

    __slots__ = ("town_hall",)

    def __init__(self, *, data, client):
        super().__init__(data=data, client=client)
        self.town_hall = data.get("townHallLevel")

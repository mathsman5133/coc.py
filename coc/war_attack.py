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

if typing.TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .war_members import ClanWarMember


class WarAttack:
    """Represents a Clash of Clans War Attack

    Attributes
    ----------
    war:
        :class:`ClanWar` - The war this attack belongs to
    stars:
        :class:`int` - The stars achieved
    destruction:
        :class:`float` - The destruction achieved as a percentage (of 100)
    order:
        :class:`int` - The attack order in this war
    attacker_tag:
        :class:`str` - The attacker tag
    defender_tag:
        :class:`str` - The defender tag
    duration:
        :class:`int` - Duration of attack in seconds
    """

    __slots__ = ("war",
                 "member",
                 "stars",
                 "destruction",
                 "order",
                 "attacker_tag",
                 "defender_tag",
                 "duration",
                 "_raw_data",
                 "_client")

    def __repr__(self):
        attrs = [
            ("war", repr(self.war)),
            ("attacker_tag", self.attacker_tag),
            ("defender_tag", self.defender_tag),
            ("stars", self.stars),
            ("destruction", self.destruction),
            ("order", self.order),
            ("duration", self.duration),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __hash__(self):
        return hash(self.attacker_tag) << self.order

    def __eq__(self, other):
        # potential future bug: because I'm comparing attacker tag, defender tag and order,
        # if the same 2 clans go into war again in the future,
        # and the same people attack each other at the same order in war and
        # you're trying to compare attacks from the first war (stored in db) and the future war (live)
        # then it's gonna think they're equal.
        # I can't use war.start_time in case prep or something changes
        # and then it will muck up on war attack for a lot of attacks
        return (
            isinstance(other, self.__class__)
            and self.attacker_tag == other.attacker_tag
            and self.defender_tag == other.defender_tag
            and self.order == other.order
        )

    def __init__(self, *, data, client, war):
        self.war = war
        self._raw_data = data if client and client.raw_attribute else None
        self._client = client
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.stars: int = data["stars"]
        self.destruction: float = data["destructionPercentage"]
        self.order: int = data["order"]
        self.attacker_tag: str = data["attackerTag"]
        self.defender_tag: str = data["defenderTag"]
        self.duration: float = data["duration"]

    @property
    def attacker(self) -> "ClanWarMember":
        """:class:`ClanWarMember`: Returns the attacking player."""
        return self.war.get_member(self.attacker_tag)

    @property
    def defender(self) -> "ClanWarMember":
        """:class:`ClanWarMember`: Returns the defending player."""
        return self.war.get_member(self.defender_tag)

    @property
    def is_fresh_attack(self) -> bool:
        """:class:`boolean`: Returns whether the attack is a fresh (first) attack on the defender."""
        if len(self.defender.defenses) == 1:
            # fast route
            return True

        return min(defense.order for defense in self.defender.defenses) == self.order

class WarAttack:
    """Represents a Clash of Clans War Attack

    Attributes
    -----------
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
    """

    __slots__ = ("war", "member", "stars", "destruction", "order", "attacker_tag", "defender_tag", "_client")

    def __repr__(self):
        attrs = [
            ("war", repr(self.war)),
            ("member", repr(self.member)),
            ("stars", self.stars),
            ("destruction", self.destruction),
            ("order", self.order),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, client, war):
        self.war = war
        self._client = client
        self._from_data(data)

    def _from_data(self, data):
        self.stars = data["stars"]
        self.destruction = data["destructionPercentage"]
        self.order = data["order"]
        self.attacker_tag = data["attackerTag"]
        self.defender_tag = data["defenderTag"]

    @property
    def attacker(self):
        """:class:`WarMember`: Returns the attacking player."""
        return self.war.get_player(self.attacker_tag)

    @property
    def defender(self):
        """:class:`WarMember`: Returns the defending player."""
        return self.war.get_player(self.defender_tag)

    @property
    def is_fresh_attack(self):
        """:class:`boolean`: Returns whether the attack is a fresh (first) attack on the defender."""
        if len(self.defender.defenses) == 1:
            # fast route
            return True

        return min(defense.order for defense in self.defender.defenses) == self.order

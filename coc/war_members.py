from .abc import BasePlayer
from .war_attack import WarAttack


class ClanWarMember(BasePlayer):
    """Represents a War Member that the API returns.
    Depending on which method calls this, some attributes may
    be ``None``.

    Attributes
    -----------
    town_hall:
        :class:`int`: The member's townhall level.
    map_position:
        :class:`int`: The member's map position in the war.
    defense_count:
        :class:`int`: The number of times this member has been attacked.
    war:
        :class:`War`: The current war this member is in.
    clan:
        :class:`WarClan`: The member's clan.
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
        "_client",
    )

    def __init__(self, *, data, client, war, clan):
        super().__init__(data=data, client=client)
        self._client = client
        self._attacks = []
        self.war = war
        self.clan = clan
        self._from_data(data)

    def _from_data(self, data):
        data_get = data.get

        self.name = data_get("name")
        self.tag = data_get("tag")
        self.town_hall = data_get("townhallLevel")
        self.map_position = data_get("mapPosition")
        self.defense_count = data_get("opponentAttacks")

        self.__iter_attacks = (
            WarAttack(data=adata, client=self._client, war=self.war) for adata in data_get("attacks", [])
        )

        boa_data = data_get("bestOpponentAttack")
        if boa_data:
            self._best_opponent_attacker = boa_data.get("attackerTag")

    @property
    def best_opponent_attack(self):
        """:class:`WarAttack`: Returns the best opponent attack on this base."""
        return self.war._get_attack((self._best_opponent_attacker, self.tag))

    @property
    def attacks(self):
        """List[:class:`WarAttack`]: The member's attacks this war. Could be an empty list."""
        list_attacks = self._attacks
        if list_attacks:
            return list_attacks

        list_attacks = self._attacks = list(self.__iter_attacks)
        return list_attacks

    @property
    def defenses(self):
        """List[:class:`WarAttack`]: The member's defenses this war. Could be an empty list."""
        return self.war.get_defenses(self.tag)

    @property
    def is_opponent(self):
        """Bool: Indicates whether the member is from the opponent clan or not."""
        return self.clan and self.war.opponent and self.clan.tag == self.war.opponent.tag


class ClanWarLeagueClanMember(BasePlayer):
    __slots__ = ("town_hall",)

    def __init__(self, *, data, client):
        super().__init__(data=data, client=client)
        self.town_hall = data.get("townHallLevel")

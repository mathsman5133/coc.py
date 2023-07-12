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
from typing import List, TYPE_CHECKING

from . import BasePlayer
from .miscmodels import Badge, Timestamp, try_enum
from .utils import cached_property, correct_tag

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .war_members import ClanWarMember  # noqa


class RaidMember(BasePlayer):
    """Represents a Raid Member that the API returns.

    Attributes
    ----------
    tag: :class:`str`
        The player's tag
    name: :class:`str`
        The player's name
    attack_count: :class:`int`
        The number of attacks from this player
    attack_limit: :class:`int`
        The limit of attacks from this player
    bonus_attack_limit: :class:`int`
        The limit of bonus attacks from this player
    capital_resources_looted:  :class:`int`
        The amount of resources looted by this player
    raid_log_entry: :class:`RaidLogEntry`
        The raid log entry this member is in
    """

    __slots__ = ("tag",
                 "name",
                 "attack_count",
                 "attack_limit",
                 "bonus_attack_limit",
                 "capital_resources_looted",
                 "raid_log_entry",
                 "_cs_attacks",
                 "_client")

    def __init__(self, *, data, client, raid_log_entry):
        super().__init__(data=data, client=client)
        self._client = client
        self.raid_log_entry = raid_log_entry
        self._from_data(data)

    def __repr__(self):
        attrs = [
            ("tag", self.tag),
            ("raid_log_entry", repr(self.raid_log_entry)),
            ("attack_count", self.attack_count)
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, RaidMember)
                and self.tag == other.tag
                and self.raid_log_entry == other.raid_log_entry)

    def _from_data(self, data):
        data_get = data.get

        self.name: str = data_get("name")
        self.tag: str = data_get("tag")
        self.attack_count: int = data_get("attacks")
        self.attack_limit: int = data_get("attackLimit")
        self.bonus_attack_limit: int = data_get("bonusAttackLimit")
        self.capital_resources_looted: int = data_get("capitalResourcesLooted")

    @cached_property("_cs_attacks")
    def attacks(self):
        """List[:class:`RaidAttack`]: The member's attacks in this raid log entry.
        Can be empty due to missing parts in the API response.
        """
        return list(attack for attack_raid in self.raid_log_entry.attack_log
                    for district in attack_raid.districts for attack in district.attacks
                    if attack and attack.attacker_tag == self.tag)


class RaidAttack:
    """Represents a Raid attack

    Attributes
    ----------
    attacker_tag:
        :class:`str` - The attacker tag
    attacker_name:
        :class:`str` - The attacker name
    destruction:
        :class:`float`- The destruction achieved
    raid_log_entry:
        :class:`RaidLogEntry` - The raid log entry this attack belongs to
    raid_clan:
        :class:`RaidClan` - The raid clan this attack belongs to
    district:
        :class:`RaidDistrict` - The raid district this attack belongs to
    stars:
        :class:`int` - The raid attacks stars
    """

    __slots__ = ("raid_log_entry",
                 "raid_clan",
                 "district",
                 "raid_member",
                 "attacker_tag",
                 "attacker_name",
                 "destruction",
                 "stars",
                 "_client",
                 "_raw_data",
                 )

    def __repr__(self):
        attrs = [
            ("raid_log_entry", repr(self.raid_log_entry)),
            ("raid_clan", repr(self.raid_clan)),
            ("district", repr(self.district)),
            ("attacker_tag", self.attacker_tag),
            ("destruction", self.destruction),
            ("stars", self.stars),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, RaidAttack)
                and self.attacker_tag == other.attacker_tag
                and self.destruction == other.destruction
                and self.raid_clan == other.raid_clan
                and self.district == other.district
                and self.stars == other.stars)

    def __init__(self, data, client, raid_log_entry, raid_clan, district):
        self.raid_log_entry = raid_log_entry
        self.raid_clan = raid_clan
        self.district = district
        self._client = client
        self._raw_data = data if client and client.raw_attribute else None
        self._from_data(data)

    def _from_data(self, data: dict) -> None:
        self.attacker_tag = data["attacker"]["tag"]
        self.attacker_name = data["attacker"]["name"]
        self.destruction = data["destructionPercent"]
        self.stars = data["stars"]

    @property
    def attacker(self) -> "RaidMember":
        """:class:`RaidMember`: Returns the attacking player."""
        return self.raid_log_entry.get_member(self.attacker_tag)


class RaidDistrict:
    """Represents a Raid Clan Capital District.

    Attributes
    -----------
    id:
        :class:`int`: The district's unique ID as given by the API.
    name:
        :class:`str`: The district's name.
    hall_level:
        :class:`str`: The district's hall level.
    destruction:
        :class:`float`: The districts destruction percentage
    attack_count:
        :class:`int`: The districts attack count
    looted:
        :class:`int`: The districts total looted
    attacks:
        List[:class:`RaidAttack`]: The attacks on this district. Can be empty due to missing parts in the api response
    raid_log_entry:
        :class:`RaidLogEntry` - The raid log entry this district belongs to
    raid_clan:
        :class:`RaidClan` - The raid clan this district belongs to
    """

    def __eq__(self, other):
        return (isinstance(other, RaidDistrict)
                and self.id == other.id
                and self.raid_clan == other.raid_clan)

    __slots__ = ("id",
                 "name",
                 "hall_level",
                 "stars",
                 "destruction",
                 "attack_count",
                 "looted",
                 "attacks",
                 "raid_log_entry",
                 "raid_clan",
                 "_client",
                 "_raw_data")

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = [("id", self.id),
                 ("raid_log_entry", repr(self.raid_log_entry)),
                 ("raid_clan", repr(self.raid_clan)),
                 ("hall_level", self.hall_level),
                 ("stars", self.stars),
                 ("destruction", self.destruction)]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __init__(self, *, data, client, raid_log_entry, raid_clan):
        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.hall_level: int = data.get("districtHallLevel")
        self.stars: int = data.get("stars")
        self.destruction: float = data.get("destructionPercent")
        self.attack_count: int = data.get("attackCount")
        self.looted: int = data.get("totalLooted")
        self.raid_log_entry = raid_log_entry  # type: RaidLogEntry
        self.raid_clan = raid_clan  # type: RaidClan
        self._raw_data = data if client and client.raw_attribute else None
        self._client = client
        if data.get("attacks", None):
            self.attacks: List[RaidAttack] = [RaidAttack(data=adata, client=client,
                                                         raid_log_entry=self.raid_log_entry,
                                                         raid_clan=self.raid_clan, district=self)
                                              for adata in data.get("attacks")]
        else:
            self.attacks = []
        if self.destruction != 0 and self.stars == 0:  # attempt to fix an api bug responding with the wrong star count
            self.stars = max(*[a.stars for a in self.attacks if a], self.stars)


class RaidClan:
    """Represents the clan object returned by clan raid seasons.

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
        attack_count: :class:`int`
            The number of attacks in the raid.
        district_count: :class:`int`
            The number of districts in the raid.
        destroyed_district_count: :class:`int`
            The number of destroyed districts in the raid.
        index:
            :class:`int` - The index/order of the raid clan in the raid weekend
        raid_log_entry:
            :class:`RaidLogEntry` - The raid log entry this attack belongs to
        """

    __slots__ = (
        "tag",
        "name",
        "badge",
        "level",
        "index",
        "attack_count",
        "district_count",
        "destroyed_district_count",
        "raid_log_entry",
        "_districts",
        "_attacks",
        "_client",
        "_response_retry",
        "_cs_raid_attacks",
        "_cs_raid_districts",
        "_cs_looted",
        "_iter_raid_districts",
        "_raw_data"
    )

    def __init__(self, *, data, client, raid_log_entry, index=0, **_):
        self._client = client
        self._raw_data = data if client and client.raw_attribute else None
        self._response_retry = data.get("_response_retry")
        self.tag = data.get("attacker", data.get("defender")).get("tag")
        self.name = data.get("attacker", data.get("defender")).get("name")
        self.badge = try_enum(Badge, data=data.get("attacker", data.get("defender")).get("badgeUrls"),
                              client=self._client)
        self.level = data.get("attacker", data.get("defender")).get("level")
        self.raid_log_entry = raid_log_entry
        self.index = index
        self._from_data(data)

    def __eq__(self, other):
        return (isinstance(other, RaidClan)
                and self.tag == other.tag
                and self.raid_log_entry.start_time == other.raid_log_entry.start_time
                and self.index == other.index)

    def __repr__(self):
        attrs = [
            ("tag", self.tag),
            ("name", self.name),
            ("raid_log_entry", repr(self.raid_log_entry))
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data):
        data_get = data.get

        self.attack_count: int = data_get("attackCount")
        self.district_count: int = data_get("districtCount")
        self.destroyed_district_count: int = data_get("districtsDestroyed")

        if data_get("districts"):
            self._iter_raid_districts = (RaidDistrict(data=data, client=self._client,
                                                      raid_log_entry=self.raid_log_entry, raid_clan=self) for
                                         data in data_get("districts"))
        else:
            self._iter_raid_districts = ()

    @cached_property("_cs_raid_districts")
    def districts(self) -> typing.List[RaidDistrict]:
        """List[:class:`RaidDistrict`]: A :class:`List` of :class:`RaidDistrict` that the clan
        attacked."""
        return list(self._iter_raid_districts)

    @cached_property("_cs_raid_attacks")
    def attacks(self) -> typing.List[RaidAttack]:
        """List[:class:`RaidAttack`]: Returns all attacks in the raid against this clan."""
        return list(attack for district in self.districts for attack in district.attacks)

    @cached_property("_cs_looted")
    def looted(self) -> int:
        """:class:`int`: The amount of loot the raid clan got on all districts."""
        loot = 0
        for district in self.districts:
            loot += district.looted
        return loot

    @property
    def is_finished(self) -> bool:
        return self.destroyed_district_count == self.district_count


class RaidLogEntry:
    """Represents a Clash of Clans Raid Log Entry

    Attributes
    ----------
    state:
        :class:`str`: The state of the raid log entry. Currently, the states ``ongoing`` and ``ended`` are known.
    start_time:
        :class:`Timestamp`: The :class:`Timestamp` that the raid started at.
    end_time:
        :class:`Timestamp`: The :class:`Timestamp` that the raid ended at.
    total_loot:
        :class:`int`: The amount of total loot
    completed_raid_count:
        :class:`int`: The number of completed raids
    attack_count:
        :class:`int`: The total number of attacks
    destroyed_district_count:
        :class:`int`: The number of destroyed enemy districts
    offensive_reward:
        :class:`int`: The amount of offensive reward
    defensive_reward:
        :class:`int`: The amount of defensive reward
    """

    __slots__ = ("clan_tag",
                 "state",
                 "start_time",
                 "end_time",
                 "total_loot",
                 "completed_raid_count",
                 "attack_count",
                 "destroyed_district_count",
                 "offensive_reward",
                 "defensive_reward",
                 "_raw_data",
                 "_cs_attack_log",
                 "_cs_defense_log",
                 "_cs_members",
                 "_cs_total_defensive_loot",
                 "_cs_defense_attack_count",
                 "_cs_defensive_destroyed_district_count",
                 "_iter_members",
                 "_iter_attack_log",
                 "_iter_defense_log",
                 "_members",
                 "_attack_log",
                 "_defense_log",
                 "_client",
                 "_response_retry"
                 )

    def __init__(self, *, data, client, **kwargs):
        self._client = client
        self.clan_tag = kwargs['clan_tag'] if "clan_tag" in kwargs else ""
        self._response_retry = kwargs['response_retry'] if "response_retry" in kwargs else 0
        self._raw_data = data if client and client.raw_attribute else None
        self._from_data(data)
        self._members = {}
        self._attack_log = []
        self._defense_log = []

    def __repr__(self):
        attrs = [
            ("state", self.state),
            ("start_time", self.start_time),
        ]
        return "<%s %s>" % (self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def __eq__(self, other):
        return (isinstance(other, RaidLogEntry)
                and self.start_time == other.start_time
                and self.clan_tag == other.clan_tag)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.state: str = data_get("state")
        self.start_time = try_enum(Timestamp, data=data_get("startTime"))
        self.end_time = try_enum(Timestamp, data=data_get("endTime"))
        self.total_loot: int = data_get("capitalTotalLoot")
        self.completed_raid_count: int = data_get("raidsCompleted")
        self.attack_count: int = data_get("totalAttacks")
        self.destroyed_district_count: int = data_get("enemyDistrictsDestroyed")
        self.offensive_reward: int = data_get("offensiveReward")
        self.defensive_reward: int = data_get("defensiveReward")

        self._iter_attack_log = (RaidClan(data=adata, raid_log_entry=self, client=self._client, index=c)
                                 for c, adata in enumerate(data_get("attackLog", [])))

        self._iter_defense_log = (RaidClan(data=adata, raid_log_entry=self, client=self._client, index=c)
                                  for c, adata in enumerate(data_get("defenseLog", [])))

        self._iter_members = (RaidMember(data=adata, raid_log_entry=self, client=self._client)
                              for adata in data_get("members", []))

    @cached_property("_cs_members")
    def members(self) -> typing.List[RaidMember]:
        """List[:class:`RaidMember`]: A list of members that are in the raid.
        """
        dict_members = self._members = {m.tag: m for m in self._iter_members}
        return list(dict_members.values())

    @cached_property("_cs_attack_log")
    def attack_log(self) -> typing.List[RaidClan]:
        """List[:class:`RaidClan`]: A list of raid clans that are attacked in the raid season.
        """
        list_attack_log = self._attack_log = [m for m in self._iter_attack_log]
        return list_attack_log

    @cached_property("_cs_defense_log")
    def defense_log(self) -> typing.List[RaidClan]:
        """List[:class:`RaidClan`]: A list of raid clans which represents all the defensive raids of a season.
        """
        list_defense_log = self._defense_log = [m for m in self._iter_defense_log]
        return list_defense_log

    @cached_property("_cs_total_defensive_loot")
    def total_defensive_loot(self) -> int:
        """:class:`int`: The total amount of loot taken by all opponents of the raid weekend."""
        loot = 0
        for clan in self.defense_log:
            loot += clan.looted
        return loot

    @cached_property("_cs_defense_attack_count")
    def defense_attack_count(self) -> int:
        """:class:`int`: The total amount of opponent attacks in the raid weekend."""
        count = 0
        for clan in self.defense_log:
            count += clan.attack_count
        return count

    @cached_property("_cs_defensive_destroyed_district_count")
    def defensive_destroyed_district_count(self) -> int:
        """:class:`int`: The total amount of districts destroyed by opponents."""
        count = 0
        for clan in self.defense_log:
            count += clan.destroyed_district_count
        return count

    def get_member(self, tag: str) -> typing.Optional[RaidMember]:
        """Get a member of the clan for the given tag, or ``None`` if not found.

        Returns
        --------
        The clan member who matches the tag.: Optional[:class:`RaidMember`]"""
        tag = correct_tag(tag)
        if not self._members:
            _ = self.members

        try:
            return self._members[tag]
        except KeyError:
            return None

"""
MIT License

Copyright (c) 2019 mathsman5133

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
from .players import ClanMember
from .miscmodels import try_enum, Location, Label, WarLeague
from .utils import get
from .abc import BaseClan


class Clan(BaseClan):
    __slots__ = (
        "type",
        "description",
        "location",
        "level",
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
        "__iter_labels",
        "__iter_members",
        "_members",
        "_client",
        "label_cls",
        "member_cls",
        "war_league",
    )

    def __init__(self, *, data, client, **kwargs):
        super().__init__(data=data, client=client)
        self.label_cls = Label
        self.member_cls = ClanMember

        self._labels = []
        self._members = {}

        self._from_data(data)

    def _from_data(self, data):
        data_get = data.get

        self.points = data_get("clanPoints")
        self.versus_points = data_get("clanVersusPoints")
        self.member_count = data_get("members")
        self.location = try_enum(Location, data=data_get("location"))

        # only available via /clans/{clanTag} or /clans endpoint
        self.type = data_get("type")
        self.required_trophies = data_get("requiredTrophies")
        self.war_frequency = data_get("warFrequency")
        self.war_win_streak = data_get("warWinStreak")
        self.war_wins = data_get("warWins")
        self.war_ties = data_get("warTies")
        self.war_losses = data_get("warLosses")
        self.public_war_log = data_get("isWarLogPublic")
        self.description = data_get("description")
        self.war_league = try_enum(WarLeague, data=data_get("warLeague"))

        label_cls = self.label_cls
        self.__iter_labels = (label_cls(data=ldata, client=self._client) for ldata in data_get("labels", []))

        # update members globally. only available via /clans/{clanTag}
        member_cls = self.member_cls
        self.__iter_members = (member_cls(data=mdata, client=self._client) for mdata in data_get("memberList", []))

    @property
    def labels(self):
        """List[:class:`Label`]: A :class:`List` of :class:`Label` that the clan has."""
        list_labels = self._labels
        if list_labels:
            return list_labels

        list_labels = self._labels = list(self.__iter_labels)
        return list_labels

    @property
    def members(self):
        dict_members = self._members
        if dict_members:
            return list(dict_members.values())

        dict_members = self._members = {m.tag: m for m in self.__iter_members}
        return list(dict_members.values())

    def get_member(self, tag):
        """Return a :class:`ClanMember` with the tag provided."""
        dict_members = self._members
        if not dict_members:
            dict_members = self._members = {m.name: m for m in self.__iter_members}

        try:
            return dict_members[tag]
        except KeyError:
            return None

    def get_member_by(self, **attrs):
        """Returns the first :class:`BasicPlayer` that meets the attributes passed

        This will return the first member matching the attributes passed.

        An example of this looks like:

        .. code-block:: python3

            clan = client.get_clan('clan tag')
            member = clan.get_member(name='Bob the Builder')

        This search implements the :func:`coc.utils.get` function
        """
        return get(self.members, **attrs)

import unittest

from coc.clans import Clan
from coc.miscmodels import Location, Label, WarLeague
from coc.players import ClanMember
from tests.mockdata.mock_clan import SEARCH_CLAN_MOCK


class TestClans(unittest.TestCase):
    def test_points(self):
        test_datas = [
            {"clanPoints": 1234, "clanVersusPoints": 234567},
            {"clanPoints": 555667, "clanVersusPoints": 1468},
            {"clanPoints": 345678, "clanVersusPoints": 229988},
        ]
        for data in test_datas:
            clan = Clan(data=data, client=None)
            self.assertEquals(clan.points, data["clanPoints"])

    def test_member_count(self):
        clan = Clan(data=SEARCH_CLAN_MOCK, client=None)
        self.assertEquals(clan.member_count, len(clan.members))

    def test_location(self):
        data = {"id": 32000172, "name": "Niue", "isCountry": True, "countryCode": "NU"}
        location = Location(data=data)
        clan = Clan(data=SEARCH_CLAN_MOCK, client=None)
        self.assertEquals(clan.location, location)
        self.assertEquals(clan.location.id, location.id)

    def test_type(self):
        data = [{"type": "inviteOnly"}, {"type": "closed"}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.type, case.get("type", None))

    def test_required_trophies(self):
        data = [{"requiredTrophies": 5000}, {"requiredTrophies": 0}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.required_trophies, case.get("requiredTrophies", None))

    def test_war_frequency(self):
        data = [{"warFrequency": "always"}, {"warFrequency": "sometimes"}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.war_frequency, case.get("warFrequency", None))

    def test_war_win_streak(self):
        data = [{"warWinStreak": 65}, {"warWinStreak": 0}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.war_win_streak, case.get("warWinStreak"))

    def test_war_wins(self):
        data = [{"warWins": 52}, {"warWins": 968}, {"warWins": 0}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.war_wins, case.get("warWins"))

    def test_war_ties(self):
        data = [{"warTies": 6}, {"warTies": 42}, {"warTies": 0}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.war_ties, case.get("warTies", None))

    def test_war_losses(self):
        data = [{"warLosses": 5009}, {"warLosses": 100}, {"warLosses": 0}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.war_losses, case.get("warLosses", None))

    def test_public_war_log(self):
        data = [{"isWarLogPublic": True}, {"isWarLogPublic": False}, {}]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEquals(clan.public_war_log, case.get("isWarLogPublic"))
            if clan.public_war_log is not None:
                self.assertIsInstance(clan.public_war_log, bool)

    def test_description(self):
        data = [
            {"description": "this is a very fancy description"},
            {"description": "testing is so much fun!"},
            {"description": ""},
            {},
        ]
        for case in data:
            clan = Clan(data=case, client=None)
            self.assertEqual(clan.description, case.get("description"))
            if clan.description is not None:
                self.assertIsInstance(clan.description, str)

    def test_war_league(self):
        data = {"id": 48000013, "name": "Master League III"}
        clan = Clan(data=SEARCH_CLAN_MOCK, client=None)
        war_league = WarLeague(data=data)
        self.assertEquals(clan.war_league, war_league)
        self.assertIsInstance(clan.war_league, WarLeague)
        self.assertIsInstance(clan.war_league.id, int)
        self.assertIsInstance(clan.war_league.name, str)

    def test_labels(self):
        clan = Clan(data=SEARCH_CLAN_MOCK, client=None)
        self.assertIsInstance(clan.labels, list)

        label_ids = [
            {"id": 56000000, "name": "Clan Wars"},
            {"id": 56000001, "name": "Clan War League"},
            {"id": 56000004, "name": "Clan Games"},
        ]
        for index, label in enumerate(clan.labels):
            mock_label = Label(data=label_ids[index], client=None)
            self.assertEqual(label, mock_label)
            self.assertIsInstance(label.id, int)
            self.assertIsInstance(label.name, str)
            self.assertIsInstance(str(label), str)

    def test_members(self):
        clan = Clan(data=SEARCH_CLAN_MOCK, client=None)

        self.assertEquals(clan.member_count, len(clan.members))
        self.assertIsInstance(clan.members, list)

        for member in clan.members:
            self.assertIsInstance(member, ClanMember)

            get_member = clan.get_member(member.tag)
            self.assertEquals(member, get_member)

            by_name = clan.get_member_by(name=member.name, trophies=member.trophies)
            self.assertEquals(member, by_name)

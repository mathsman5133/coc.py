import unittest

from coc.wars import ClanWar
from coc.miscmodels import Timestamp

from tests.mockdata.mock_current_war import MOCK_CURRENT_WAR_IN_WAR


class TestWars(unittest.TestCase):
    def test_state(self):
        data = [
            {"state": "notInWar"},
            {"state": "preparation"},
            {"state": "inWar"},
            {"state": "warEnded"},
            {},
        ]
        for case in data:
            war = ClanWar(data=case, clan_tag="", client=None)
            try:
                state = case["state"]
                self.assertIsInstance(state, str)
            except KeyError:
                state = None
                self.assertIsNone(war.state)
            self.assertEqual(war.state, state)

    def test_team_size(self):
        data = [{"teamSize": 15}, {"teamSize": 30}, {"teamSize": 5}, {}]
        for case in data:
            war = ClanWar(data=case, clan_tag="", client=None)
            try:
                size = case["teamSize"]
                self.assertIsInstance(war.team_size, int)
            except KeyError:
                size = 0
                self.assertEqual(war.team_size, 0)
            self.assertEqual(war.team_size, size)

    def test_start_times(self):
        data = [
            {
                "preparationStartTime": "20200522T051229.000Z",
                "startTime": "20200523T043025.000Z",
                "endTime": "20200524T043025.000Z",
            },
        ]
        for case in data:
            war = ClanWar(data=case, clan_tag="", client=None)

            self.assertGreater(war.start_time, war.preparation_start_time)
            self.assertGreater(war.end_time, war.start_time)

            self.assertLess(war.preparation_start_time, war.start_time)
            self.assertLess(war.start_time, war.end_time)

            self.assertIsInstance(war.preparation_start_time, Timestamp)
            self.assertIsInstance(war.start_time, Timestamp)
            self.assertIsInstance(war.end_time, Timestamp)

            self.assertEqual(war.type, "random")


class TestWarClan(unittest.TestCase):
    def test_level(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

    def test_destruction(self):
        data = {"clan": {"destructionPercentage": 84.88}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.destruction, float)

    def test_exp_earned(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

    def test_clan_level(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

    def test_clan_level(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

    def test_clan_level(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

    def test_clan_level(self):
        data = {"clan": {"clanLevel": 10}}
        war = ClanWar(data=data, client=None, clan_tag=None)
        self.assertIsInstance(war.clan.level, int)

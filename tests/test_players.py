import unittest

import coc
from coc.players import Player, ClanMember
from coc.clans import Clan
from coc.player_clan import PlayerClan
from coc.enums import (
    HOME_TROOP_ORDER,
    BUILDER_TROOPS_ORDER,
    SPELL_ORDER,
    HERO_ORDER,
    ACHIEVEMENT_ORDER,
    SIEGE_MACHINE_ORDER,
)
from coc.miscmodels import League, LegendStatistics, Season, Label
from coc.enums import Role
from tests.mockdata.mock_players import MOCK_SEARCH_PLAYER, MOCK_CLAN_MEMBER


class TestClanMember(unittest.TestCase):

    def setUp(self) -> None:
        self.client = coc.Client()
        self.client._create_holders()
        
    def test_exp_level(self):
        data = {"expLevel": 241}
        member = ClanMember(data=data, client=self.client)
        self.assertEqual(member.exp_level, data["expLevel"])

        member2 = ClanMember(data=MOCK_CLAN_MEMBER, client=self.client)
        self.assertIsInstance(member2.exp_level, int)

    def test_trophies(self):
        data = [{"trophies": 5432}, {"trophies": 0}, {}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            self.assertEqual(member.trophies, case.get("trophies"))

    def test_clan_rank(self):
        data = [{"clanRank": 34}, {"clanRank": 1}, {}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            self.assertEqual(member.clan_rank, case.get("clanRank"))

    def test_clan_previous_rank(self):
        data = [{"previousClanRank": 14}, {"previousClanRank": 4}, {}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            self.assertEqual(member.clan_previous_rank, case.get("previousClanRank"))

    def test_donations(self):
        data = [{"donations": 55}, {"donations": 0}, {}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            self.assertEqual(member.donations, case.get("donations"))

    def test_received(self):
        data = [{"donationsReceived": 9876}, {"donationsReceived": 0}, {}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            self.assertEqual(member.received, case.get("donationsReceived"))

    def test_clan(self):
        data = {
            "clan": {
                "tag": "#8J8QJ2LV",
                "name": "Reddit Ace",
                "clanLevel": 18,
                "badgeUrls": {
                    "small": "https://api-assets.clashofclans.com/badges/70/thXuucdocdtfUts55bsAoGfQ0P8ghwLezzeG-UUajp0.png",
                    "large": "https://api-assets.clashofclans.com/badges/512/thXuucdocdtfUts55bsAoGfQ0P8ghwLezzeG-UUajp0.png",
                    "medium": "https://api-assets.clashofclans.com/badges/200/thXuucdocdtfUts55bsAoGfQ0P8ghwLezzeG-UUajp0.png",
                },
            }
        }
        member = ClanMember(data=data, client=self.client)
        clan = PlayerClan(data=data["clan"], client=self.client)
        self.assertEqual(member.clan, clan)
        self.assertIsInstance(member.clan, PlayerClan)

    def test_league(self):
        data = {"league": {"id": 29000022, "name": "Legend League",}}
        member = ClanMember(data=data, client=self.client)
        league = League(data=data["league"], client=self.client)
        self.assertEqual(member.league, league)
        self.assertIsInstance(member.league, League)

    def test_role(self):
        data = [{"role": "member"}, {"role": "admin"}, {"role": "coLeader"}, {"role": "leader"}]
        for case in data:
            member = ClanMember(data=case, client=self.client)
            role = Role(case["role"])
            self.assertEqual(member.role, role)
            self.assertIsInstance(member.role, Role)
            role_readable = str(role)
            self.assertIsInstance(role_readable, str)
            self.assertNotEqual(role_readable, role)


class TestPlayers(unittest.TestCase):

    def setUp(self) -> None:
        self.client = coc.Client()
        self.client._create_holders()

    def test_best_trophies(self):
        data = [{"bestTrophies": 5600}, {"bestTrophies": 0}, {}]
        for case in data:
            player = Player(data=case, client=self.client)
            self.assertEqual(player.best_trophies, case.get("bestTrophies"))

    def test_war_stars(self):
        data = [{"warStars": 1234}, {"warStars": 0}, {}]
        for case in data:
            player = Player(data=case, client=self.client)
            self.assertEqual(player.war_stars, case.get("warStars"))

    def test_town_hall(self):
        data = [{"townHallLevel": 13}, {"townHallLevel": 6}, {}]
        for case in data:
            player = Player(data=case, client=self.client)
            self.assertEqual(player.town_hall, case.get("townHallLevel"))

    def test_town_hall_weapon(self):
        data = [{"townHallWeaponLevel": 4}, {"townHallWeaponLevel": 0}, {}]
        for case in data:
            player = Player(data=case, client=self.client)
            self.assertEqual(player.town_hall_weapon, case.get("townHallWeaponLevel"))

    def test_builder_hall(self):
        data = [{"builderHallLevel": 8}, {"builderHallLevel": 0}, {}]
        for case in data:
            player = Player(data=case, client=self.client)
            self.assertEqual(player.builder_hall, case.get("builderHallLevel", 0))


    def test_legend_statistics(self):
        data = {
            "legendStatistics": {
                "legendTrophies": 4460,
                "bestSeason": {"id": "2016-01", "rank": 3708, "trophies": 5085},
                "bestVersusSeason": {"id": "2018-06", "rank": 19207, "trophies": 4827},
                "currentSeason": {"rank": 69, "trophies": 5470},
            }
        }
        player = Player(data=data, client=self.client)
        stats = LegendStatistics(data=data["legendStatistics"])
        self.assertEqual(player.legend_statistics, stats)
        self.assertIsInstance(player.legend_statistics, LegendStatistics)
        self.assertIsInstance(player.legend_statistics.legend_trophies, int)
        self.assertIsInstance(player.legend_statistics.best_season, Season)
        self.assertNotEqual(player.legend_statistics.current_season, player.legend_statistics.previous_season)

    def test_labels(self):
        data = [
            {"id": 57000000, "name": "Clan Wars"},
            {"id": 57000001, "name": "Clan War League"},
            {"id": 57000015, "name": "Veteran"},
        ]
        player = Player(data=MOCK_SEARCH_PLAYER, client=self.client)
        for index, case in enumerate(data):
            label = Label(data=case, client=self.client)
            self.assertEqual(player.labels[index], label)
            self.assertIsInstance(player.labels[index], Label)

        self.assertIsInstance(player.labels, list)

    def test_achievements(self):
        player = Player(data=MOCK_SEARCH_PLAYER, client=self.client)
        self.assertIsInstance(player.achievements, list)

        valid_achievement_order = [n for n in ACHIEVEMENT_ORDER if n in set(a.name for a in player.achievements)]

        for index, achievement in enumerate(player.achievements):
            self.assertIsInstance(achievement, player.achievement_cls)
            self.assertEqual(achievement.name, valid_achievement_order[index])
            get_achievement = player.get_achievement(achievement.name)
            self.assertEqual(get_achievement, achievement)

        get_nonsense_achievement = player.get_achievement("this is a nonsense string")
        self.assertIsNone(get_nonsense_achievement)

    def test_troops(self):
        player = Player(data=MOCK_SEARCH_PLAYER, client=self.client)
        self.assertIsInstance(player.troops, list)

        for troop in player.troops:
            self.assertIsInstance(troop, (player.troop_cls, coc.abc.DataContainer))

        # we can't use the full HOME_TROOP_ORDER in case the player hasn't unlocked a specific troop
        troop_names = set(t.name for t in player.troops)
        valid_home_troop_order = [name for name in HOME_TROOP_ORDER if name in troop_names]
        valid_builder_troop_order = [name for name in BUILDER_TROOPS_ORDER if name in troop_names]
        valid_siege_machine_order = [name for name in SIEGE_MACHINE_ORDER if name in troop_names]

        for index, troop in enumerate(player.home_troops):
            self.assertIn(troop, player.troops)
            self.assertTrue(troop.is_home_base)
            self.assertIsInstance(troop, (player.troop_cls, coc.abc.DataContainer))
            self.assertEqual(troop.name, valid_home_troop_order[index])

        for index, troop in enumerate(player.builder_troops):
            self.assertIn(troop, player.troops)
            self.assertTrue(troop.is_builder_base)
            self.assertIsInstance(troop, (player.troop_cls, coc.abc.DataContainer))
            self.assertEqual(troop.name, valid_builder_troop_order[index])

        for index, troop in enumerate(player.siege_machines):
            self.assertIn(troop, player.troops)
            self.assertTrue(troop.is_home_base)
            self.assertIsInstance(troop, (player.troop_cls, coc.abc.DataContainer))
            self.assertEqual(troop.name, valid_siege_machine_order[index])

    def test_heroes(self):
        player = Player(data=MOCK_SEARCH_PLAYER, client=self.client)
        self.assertIsInstance(player.heroes, list)

        valid_hero_order = [n for n in HERO_ORDER if n in set(h.name for h in player.heroes)]

        for index, hero in enumerate(player.heroes):
            self.assertIsInstance(hero, (player.hero_cls, coc.abc.DataContainer))
            self.assertEqual(hero.name, valid_hero_order[index])

            get_hero = player.get_hero(hero.name)
            self.assertEqual(hero, get_hero)

        get_nonsense_hero = player.get_hero("this is a nonsense string")
        self.assertIsNone(get_nonsense_hero)

    def test_spells(self):
        player = Player(data=MOCK_SEARCH_PLAYER, client=self.client)
        self.assertIsInstance(player.spells, list)

        for index, spell in enumerate(player.spells):
            self.assertIsInstance(spell, (player.spell_cls, coc.abc.DataContainer))
            self.assertEqual(spell.name, SPELL_ORDER[index])


if __name__ == '__main__':
    unittest.main()
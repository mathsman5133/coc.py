import unittest
from pathlib import Path

import ujson

from coc.clans import Clan
from coc.miscmodels import Location, Label, BaseLeague, ChatLanguage, CapitalDistrict
from coc.players import ClanMember

import tracemalloc

tracemalloc.start()

with open(Path(__file__).parent.joinpath(Path("mockdata/clans/clans/CLAN.json")), encoding="utf-8") as fp:
	MOCK_CLAN = ujson.load(fp)

with open(Path(__file__).parent.joinpath(Path("mockdata/clans/search/CLANS_FOUND.json")), encoding="utf-8") as fp:
	MOCK_SEARCH_CLAN = ujson.load(fp)


class TestClans(unittest.TestCase):
	def test_points(self):
		test_datas = [{"clanPoints": 1234, "clanVersusPoints": 234567},
			{"clanPoints": 555667, "clanVersusPoints": 1468}, {"clanPoints": 345678, "clanVersusPoints": 229988}, ]
		for data in test_datas:
			clan = Clan(data=data, client=None)
			self.assertEqual(clan.points, data["clanPoints"])

	def test_member_count(self):
		clan = Clan(data=MOCK_CLAN["body"], client=None)
		self.assertEqual(clan.member_count, MOCK_CLAN["body"]["members"])
		self.assertEqual(len(clan.members), len(MOCK_CLAN["body"]["memberList"]))

	def test_location(self):
		location = Location(data=MOCK_CLAN["body"]["location"])
		clan = Clan(data=MOCK_CLAN["body"], client=None)
		self.assertEqual(clan.location, location)
		self.assertEqual(clan.location.id, location.id)

	def test_type(self):
		data = [{"type": "inviteOnly"}, {"type": "closed"}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.type, case.get("type", None))

	def test_required_trophies(self):
		data = [{"requiredTrophies": 5000}, {"requiredTrophies": 0}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.required_trophies, case.get("requiredTrophies", None))

	def test_war_frequency(self):
		data = [{"warFrequency": "always"}, {"warFrequency": "sometimes"}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.war_frequency, case.get("warFrequency", None))

	def test_war_win_streak(self):
		data = [{"warWinStreak": 65}, {"warWinStreak": 0}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.war_win_streak, case.get("warWinStreak"))

	def test_war_wins(self):
		data = [{"warWins": 52}, {"warWins": 968}, {"warWins": 0}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.war_wins, case.get("warWins"))

	def test_war_ties(self):
		data = [{"warTies": 6}, {"warTies": 42}, {"warTies": 0}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.war_ties, case.get("warTies", -1))

	def test_war_losses(self):
		data = [{"warLosses": 5009}, {"warLosses": 100}, {"warLosses": 0}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.war_losses, case.get("warLosses", -1))

	def test_public_war_log(self):
		data = [{"isWarLogPublic": True}, {"isWarLogPublic": False}, {}]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.public_war_log, case.get("isWarLogPublic"))
			if clan.public_war_log is not None:
				self.assertIsInstance(clan.public_war_log, bool)

	def test_description(self):
		data = [{"description": "this is a very fancy description"}, {"description": "testing is so much fun!"},
			{"description": ""}, {}, ]
		for case in data:
			clan = Clan(data=case, client=None)
			self.assertEqual(clan.description, case.get("description"))
			if clan.description is not None:
				self.assertIsInstance(clan.description, str)

	def test_war_league(self):
		clan = Clan(data=MOCK_CLAN["body"], client=None)
		war_league = BaseLeague(data=MOCK_CLAN["body"]["warLeague"])
		self.assertEqual(clan.war_league, war_league)
		self.assertIsInstance(clan.war_league, BaseLeague)
		self.assertIsInstance(clan.war_league.id, int)
		self.assertIsInstance(clan.war_league.name, str)

	def test_labels(self):
		clan = Clan(data=MOCK_CLAN["body"], client=None)
		self.assertIsInstance(clan.labels, list)

		label_ids = [{"id": 56000000, "name": "Clan Wars"}, {"id": 56000001, "name": "Clan War League"},
			{"id": 56000016, "name": "Clan Capital"}, ]
		for index, label in enumerate(clan.labels):
			mock_label = Label(data=label_ids[index], client=None)
			self.assertEqual(label, mock_label)
			self.assertIsInstance(label.id, int)
			self.assertIsInstance(label.name, str)
			self.assertIsInstance(str(label), str)

	def test_members(self):
		clan = Clan(data=MOCK_CLAN["body"], client=None)

		self.assertEqual(clan.member_count, len(clan.members))
		self.assertIsInstance(clan.members, list)

		for member in clan.members:
			self.assertIsInstance(member, ClanMember)

			get_member = clan.get_member(member.tag)
			self.assertEqual(member, get_member)

			by_name = clan.get_member_by(name=member.name, trophies=member.trophies)
			self.assertEqual(member, by_name)

	def test_clans_all_attributes(self):
		data = MOCK_CLAN["body"]
		clan = Clan(data=data, client=None)
		map_raw_to_cocpy = {"tag"  : "tag", "name": "name", "type": "type", "description": "description",
			"isFamilyFriendly"     : "family_friendly", "clanLevel": "level", "clanPoints": "points",
			"clanBuilderBasePoints": "builder_base_points", "clanCapitalPoints": "capital_points",
			"requiredTrophies"     : "required_trophies", "warFrequency": "war_frequency",
			"warWinStreak"         : "war_win_streak", "warWins": "war_wins", "isWarLogPublic": "public_war_log",
			"members"              : "member_count", "requiredBuilderBaseTrophies": "required_builder_base_trophies",
			"requiredTownhallLevel": "required_townhall"}

		for k, v in map_raw_to_cocpy.items():
			self.assertEqual(data.get(k), clan.__getattribute__(v))

		# test all non trivial attributes

		# test members
		self.assertIsInstance(clan.members, list)
		for member in clan.members:
			self.assertIsInstance(member, ClanMember)

			get_member = clan.get_member(member.tag)
			self.assertEqual(member, get_member)

			by_name = clan.get_member_by(name=member.name, trophies=member.trophies)
			self.assertEqual(member, by_name)

		# test labels
		self.assertIsInstance(clan.labels, list)
		label_data = data.get("labels")
		for index in range(len(label_data)):
			mock_label = Label(data=label_data[index], client=None)
			self.assertEqual(clan.labels[index], mock_label)
			self.assertIsInstance(clan.labels[index].id, int)
			self.assertIsInstance(clan.labels[index].name, str)
			self.assertIsInstance(str(clan.labels[index]), str)

		# test chat language
		self.assertIsInstance(clan.chat_language, ChatLanguage)
		self.assertEqual(clan.chat_language.id, data.get("chatLanguage", {}).get("id"))
		self.assertEqual(clan.chat_language.name, data.get("chatLanguage", {}).get("name"))
		self.assertEqual(clan.chat_language.language_code, data.get("chatLanguage", {}).get("languageCode"))

		# test badges
		self.assertEqual(clan.badge.small, data.get("badgeUrls", {}).get("small"))
		self.assertEqual(clan.badge.medium, data.get("badgeUrls", {}).get("medium"))
		self.assertEqual(clan.badge.url, data.get("badgeUrls", {}).get("medium"))
		self.assertEqual(clan.badge.large, data.get("badgeUrls", {}).get("large"))

		# test capital league
		c_league = BaseLeague(data=data["capitalLeague"])
		self.assertEqual(clan.capital_league, c_league)
		self.assertIsInstance(clan.capital_league, BaseLeague)
		self.assertIsInstance(clan.capital_league.id, int)
		self.assertIsInstance(clan.capital_league.name, str)

		# test war league
		war_league = BaseLeague(data=data["warLeague"])
		self.assertEqual(clan.war_league, war_league)
		self.assertIsInstance(clan.war_league, BaseLeague)
		self.assertIsInstance(clan.war_league.id, int)
		self.assertIsInstance(clan.war_league.name, str)

		# test location
		location = Location(data=data["location"])
		self.assertEqual(clan.location, location)
		self.assertEqual(clan.location.id, location.id)

		# test capital districts
		district_data = data.get("clanCapital", {}).get("districts", [])
		for index in range(len(district_data)):
			mock_district = CapitalDistrict(data=district_data[index], client=None)
			self.assertEqual(clan.capital_districts[index], mock_district)
			self.assertIsInstance(clan.capital_districts[index].id, int)
			self.assertIsInstance(clan.capital_districts[index].name, str)
			self.assertIsInstance(str(clan.capital_districts[index]), str)

	def test_search_all_attributes(self):
		datas = MOCK_SEARCH_CLAN["body"]["items"]
		for data in datas:
			clan = Clan(data=data, client=None)
			map_raw_to_cocpy = {"tag"        : "tag", "name": "name", "type": "type", "description": "description",
				"isFamilyFriendly"           : "family_friendly", "clanLevel": "level", "clanPoints": "points",
				"clanBuilderBasePoints"      : "builder_base_points", "clanCapitalPoints": "capital_points",
				"requiredTrophies"           : "required_trophies", "warFrequency": "war_frequency",
				"warWinStreak"               : "war_win_streak", "warWins": "war_wins",
				"isWarLogPublic"             : "public_war_log", "members": "member_count",
				"requiredBuilderBaseTrophies": "required_builder_base_trophies",
				"requiredTownhallLevel"      : "required_townhall"}

			for k, v in map_raw_to_cocpy.items():
				self.assertEqual(data.get(k), clan.__getattribute__(v))

			# test all non trivial attributes

			# test members
			self.assertIsInstance(clan.members, list)
			for member in clan.members:
				self.assertIsInstance(member, ClanMember)

				get_member = clan.get_member(member.tag)
				self.assertEqual(member, get_member)

				by_name = clan.get_member_by(name=member.name, trophies=member.trophies)
				self.assertEqual(member, by_name)

			# test labels
			self.assertIsInstance(clan.labels, list)
			label_data = data.get("labels", [])
			for index in range(len(label_data)):
				mock_label = Label(data=label_data[index], client=None)
				self.assertEqual(clan.labels[index], mock_label)
				self.assertIsInstance(clan.labels[index].id, int)
				self.assertIsInstance(clan.labels[index].name, str)
				self.assertIsInstance(str(clan.labels[index]), str)

			# test chat language
			if data.get("chatLanguage"):
				self.assertIsInstance(clan.chat_language, ChatLanguage)
				self.assertEqual(clan.chat_language.id, data.get("chatLanguage", {}).get("id"))
				self.assertEqual(clan.chat_language.name, data.get("chatLanguage", {}).get("name"))
				self.assertEqual(clan.chat_language.language_code, data.get("chatLanguage", {}).get("languageCode"))

			# test badges
			self.assertEqual(clan.badge.small, data.get("badgeUrls", {}).get("small"))
			self.assertEqual(clan.badge.medium, data.get("badgeUrls", {}).get("medium"))
			self.assertEqual(clan.badge.url, data.get("badgeUrls", {}).get("medium"))
			self.assertEqual(clan.badge.large, data.get("badgeUrls", {}).get("large"))

			# test capital league
			c_league = BaseLeague(data=data["capitalLeague"])
			self.assertEqual(clan.capital_league, c_league)
			self.assertIsInstance(clan.capital_league, BaseLeague)
			self.assertIsInstance(clan.capital_league.id, int)
			self.assertIsInstance(clan.capital_league.name, str)

			# test war league
			war_league = BaseLeague(data=data["warLeague"])
			self.assertEqual(clan.war_league, war_league)
			self.assertIsInstance(clan.war_league, BaseLeague)
			self.assertIsInstance(clan.war_league.id, int)
			self.assertIsInstance(clan.war_league.name, str)

			# test location
			location = Location(data=data["location"])
			self.assertEqual(clan.location, location)
			self.assertEqual(clan.location.id, location.id)

			# test capital districts
			district_data = data.get("clanCapital", {}).get("districts", [])
			for index in range(len(district_data)):
				mock_district = CapitalDistrict(data=district_data[index], client=None)
				self.assertEqual(clan.capital_districts[index], mock_district)
				self.assertIsInstance(clan.capital_districts[index].id, int)
				self.assertIsInstance(clan.capital_districts[index].name, str)
				self.assertIsInstance(str(clan.capital_districts[index]), str)

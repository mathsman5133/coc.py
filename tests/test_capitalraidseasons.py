import json
import unittest
from pathlib import Path

import ujson

from coc import RaidLogEntry, RaidClan, RaidAttack, RaidMember
from coc.entry_logs import RaidLog

import tracemalloc

tracemalloc.start()

with open(Path(__file__).parent.joinpath(Path("mockdata/clans/capitalraidseasons/CAPITALRAIDSEASON.json")),
          encoding="utf-8") as fp:
	MOCK_CAPITALRAIDSEASON = ujson.load(fp)


class TestRaids(unittest.TestCase):
	def test_raid_log(self):
		data = MOCK_CAPITALRAIDSEASON["body"]
		clan_tag = MOCK_CAPITALRAIDSEASON["clantag"]
		raidlog = RaidLog(client=None, clan_tag=clan_tag, limit=2,
		                  page=False, json_resp=data, model=RaidLogEntry)
		# test last raid log entry
		self.test_raidlog_entry(raidlog[0], data["items"][0])

		# test second last raid log entry
		self.test_raidlog_entry(raidlog[1], data["items"][1])

	def test_raidlog_entry(self, raidlogentry, mock_data):
		map_raw_to_cocpy = {
			"state"                  : "state",
			"capitalTotalLoot"       : "total_loot",
			"raidsCompleted"         : "completed_raid_count",
			"totalAttacks"           : "attack_count",
			"enemyDistrictsDestroyed": "destroyed_district_count",
			"offensiveReward"        : "offensive_reward",
			"defensiveReward"        : "defensive_reward"
		}
		for k, v in map_raw_to_cocpy.items():
			self.assertEqual(mock_data.get(k), raidlogentry.__getattribute__(v),
			                 f'{k=} {v=} {mock_data.get(k)=} {raidlogentry.__getattribute__(v)}')

		# test non trivial data

		# test start time
		self.assertEqual(mock_data.get("startTime"), raidlogentry.start_time.raw_time)

		# test end time
		self.assertEqual(mock_data.get("endTime"), raidlogentry.end_time.raw_time)

		# test attack log
		for c, adata in enumerate(mock_data.get("attackLog", [])):
			self.test_raid_clan(raidlogentry.attack_log[c], adata, c)

		# test defense log
		for c, adata in enumerate(mock_data.get("defenseLog", [])):
			self.test_raid_clan(raidlogentry.defense_log[c], adata, c)

		# test members
		for member in mock_data.get("members", []):
			self.test_raid_member(raidlogentry, member)

			# test member attacks
			mock_attacks = [attack for attack_raid in mock_data.get("attackLog", []) for district in attack_raid.get(
					"districts", []) for attack in district.get("attacks", [])
			                if attack and attack.get("attacker", {}).get("tag") == member.get("tag")]
			raidmember = raidlogentry.get_member(member.get("tag"))
			attacks = raidmember.attacks
			self.assertEqual(len(mock_attacks), len(attacks))
			self.assertEqual(len(mock_attacks), raidmember.attack_count)
			for attack, mock_attack in zip(attacks, mock_attacks):
				self.test_raid_attack(attack, mock_attack)

		# test defensive custom properties
		defensive_loot = raidlogentry.total_defensive_loot
		defensive_attack_count = raidlogentry.defense_attack_count
		defensive_destroyed_districts = raidlogentry.defensive_destroyed_district_count
		defensive_loot_mock = 0
		defensive_attack_count_mock = 0
		defensive_destroyed_districts_mock = 0
		for clan_data in mock_data.get("defenseLog", []):
			defensive_destroyed_districts_mock += clan_data.get("districtsDestroyed", 0)
			defensive_attack_count_mock += clan_data.get("attackCount", 0)
			for district_data in clan_data.get("districts", []):
				defensive_loot_mock += district_data.get("totalLooted", 0)
		self.assertEqual(defensive_loot, defensive_loot_mock, "RaidLogEntry.total_defensive_loot")
		self.assertEqual(defensive_attack_count, defensive_attack_count_mock, "RaidLogEntry.defense_attack_count")
		self.assertEqual(defensive_destroyed_districts, defensive_destroyed_districts_mock,
		                 "RaidLogEntry.defensive_destroyed_district_count")

	def test_raid_clan(self, raidclan: RaidClan, mock_data, index):
		map_raw_to_cocpy = {
			"attackCount"       : "attack_count",
			"districtCount"     : "district_count",
			"districtsDestroyed": "destroyed_district_count"
		}
		self.assertEqual(raidclan.tag, mock_data.get("attacker", mock_data.get("defender")).get("tag"))
		self.assertEqual(raidclan.name, mock_data.get("attacker", mock_data.get("defender")).get("name"))
		self.assertEqual(raidclan.level, mock_data.get("attacker", mock_data.get("defender")).get("level"))
		self.assertEqual(raidclan.index, index)
		for k, v in map_raw_to_cocpy.items():
			self.assertEqual(mock_data.get(k), raidclan.__getattribute__(v),
			                 f'{k=} {v=} {mock_data.get(k)=} {raidclan.__getattribute__(v)}')

		# test non trivial data

		# test raid districts
		loot_mock = 0
		destroyed_mock = 0
		for c, data in enumerate(mock_data.get("districts", [])):
			self.test_raid_district(raidclan.districts[c], data)
			loot_mock += data.get("totalLooted", 0)
			destroyed_mock += 1 if data.get("destructionPercent") == 100 else 0

		self.assertEqual(loot_mock, raidclan.looted, "looted")
		self.assertEqual(destroyed_mock == mock_data.get("districtCount"), raidclan.is_finished, "is_finished")

		# test raid clan attacks
		mock_attacks = [attack for district in mock_data.get("districts", []) for attack in district.get("attacks", [])]
		attacks = raidclan.attacks
		self.assertEqual(len(mock_attacks), len(attacks))
		for data, mock in zip(attacks, mock_attacks):
			self.test_raid_attack(data, mock)

	def test_raid_district(self, raiddistrict, mock_data):
		map_raw_to_cocpy = {
			"id"                : "id",
			"name"              : "name",
			"districtHallLevel" : "hall_level",
			"destructionPercent": "destruction",
			"attackCount"       : "attack_count",
			"totalLooted"       : "looted"
		}

		for k, v in map_raw_to_cocpy.items():
			self.assertEqual(mock_data.get(k), raiddistrict.__getattribute__(v),
			                 f'{k=} {v=} {mock_data.get(k)=} {raiddistrict.__getattribute__(v)}')

		# test non trivial data

		# test raid districts
		for c, data in enumerate(mock_data.get("attacks", [])):
			self.test_raid_attack(raiddistrict.attacks[c], data)

	def test_raid_attack(self, raidattack: RaidAttack, mock_data):
		self.assertEqual(mock_data.get("attacker", mock_data.get("defender", {})).get("tag"), raidattack.attacker_tag)
		self.assertEqual(mock_data.get("attacker", mock_data.get("defender", {})).get("name"), raidattack.attacker_name)
		self.assertEqual(mock_data.get("stars"), raidattack.stars)
		self.assertEqual(mock_data.get("destructionPercent"), raidattack.destruction)

	def test_raid_member(self, raidlogentry: RaidLogEntry, mock_data):
		raidmember = raidlogentry.get_member(mock_data.get("tag"))
		self.assertIsInstance(raidmember, RaidMember)
		self.assertEqual(raidmember.name, mock_data.get("name"))
		self.assertEqual(raidmember.attack_count, mock_data.get("attacks"))
		self.assertEqual(raidmember.attack_limit, mock_data.get("attackLimit"))
		self.assertEqual(raidmember.bonus_attack_limit, mock_data.get("bonusAttackLimit"))
		self.assertEqual(raidmember.capital_resources_looted, mock_data.get("capitalResourcesLooted"))

import unittest

from coc import RaidLogEntry, RaidClan, RaidAttack, RaidMember
from coc.entry_logs import RaidLog
from tests.mockdata.clans.mock_capitalraidseasons import MOCK_CAPITALRAIDSEASON

import tracemalloc

tracemalloc.start()


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
            "state": "state",
            "capitalTotalLoot": "total_loot",
            "raidsCompleted": "completed_raid_count",
            "totalAttacks": "attack_count",
            "enemyDistrictsDestroyed": "destroyed_district_count",
            "offensiveReward": "offensive_reward",
            "defensiveReward": "defensive_reward"
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
        
        
    def test_raid_clan(self, raidclan: RaidClan, mock_data, index):
        map_raw_to_cocpy = {
            "attackCount": "attack_count",
            "districtCount": "district_count",
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
        for c, data in enumerate(mock_data.get("districts", [])):
            self.test_raid_district(raidclan.districts[c], data)
            
    def test_raid_district(self, raiddistrict, mock_data):
        map_raw_to_cocpy = {
            "id": "id",
            "name": "name",
            "districtHallLevel": "hall_level",
            "destructionPercent": "destruction",
            "attackCount": "attack_count",
            "totalLooted": "looted"
        }

        for k, v in map_raw_to_cocpy.items():
            self.assertEqual(mock_data.get(k), raiddistrict.__getattribute__(v),
                             f'{k=} {v=} {mock_data.get(k)=} {raiddistrict.__getattribute__(v)}')

        # test non trivial data

        # test raid districts
        for c, data in enumerate(mock_data.get("attacks", [])):
            self.test_raid_attack(raiddistrict.attacks[c], data)
            
    def test_raid_attack(self, raidattack: RaidAttack, mock_data):
        self.assertEqual(mock_data.get("attacker",{}).get("tag"), raidattack.attacker_tag)
        self.assertEqual(mock_data.get("attacker",{}).get("name"), raidattack.attacker_name)
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
import unittest
import orjson
import coc

from coc.utils import UnitStatList
from coc.enums import HV_TROOP_ORDER
from coc.troop import TROOPS_FILE_PATH

import tracemalloc

tracemalloc.start()

class ClashMetaTests(unittest.TestCase):

    # def test_load_never(self):
    #     client = coc.login_with_keys("", load_game_data=coc.LoadGameData(never=True))
    #     with self.assertRaises(RuntimeError) as cm:
    #         client.parse_army_link("")
    #
    #     self.assertEqual(str(cm.exception), "Troop and Spell game metadata must be loaded to use this feature.")

    def test_load_default(self):
        client = coc.Client(load_game_data=coc.LoadGameData(default=True))
        client._create_holders()

        for holder in (client._troop_holder, client._spell_holder, client._hero_holder, client._pet_holder):
            self.assertTrue(holder.loaded)

    def test_load_startup_only(self):
        client = coc.Client(load_game_data=coc.LoadGameData(startup_only=True))
        client._create_holders()

        for holder in (client._troop_holder, client._spell_holder, client._hero_holder, client._pet_holder):
            self.assertTrue(holder.loaded)

        troop = client.get_troop("Barbarian")
        self.assertIs(type(troop), type(coc.Troop))

    def test_troop(self):
        client = coc.Client()
        client._create_holders()
        barb = client.get_troop("Barbarian")
        self.assertIs(type(barb), type(coc.Troop))

        self.assertEqual(barb.name, "Barbarian")
        self.assertIsInstance(barb.level, UnitStatList)


class TroopMeta(unittest.TestCase):
    def setUp(self) -> None:
        self.client = coc.Client()
        self.client._create_holders()
        
        ## load the characters data
        with open(TROOPS_FILE_PATH, "rb") as f:
            self.raw_troops = orjson.loads(f.read())
        
        
        self.troop = self.client.get_troop("Barbarian")
        # self.barb_i = self.client.get_troop("Barbarian", level=12)

    def test_types(self):
        self.assertIs(type(self.troop), type(coc.Troop))

    def test_levels(self):
        self.assertIsInstance(self.troop.level, UnitStatList)

        with self.assertRaises(IndexError):
            self.troop.level[0]

        self.assertEqual(len(self.troop.level), len(self.troop.lab_level))
    
    def test_troops(self):
        for troop_name in HV_TROOP_ORDER:
            troop = self.client.get_troop(troop_name)
            self.assertIs(type(troop), type(coc.Troop))
            self.assertEqual(troop.name, troop_name)
            self.assertTrue(troop.is_home_base )
            # get the raw troop data
            troop_data = self.raw_troops.get(troop.internal_name)
            self.assertEqual(troop.is_home_base and troop.is_elixir_troop, troop_data.get("ProductionBuilding") == "Barrack")
            self.assertEqual(troop.is_home_base and troop.is_dark_troop, troop_data.get("ProductionBuilding") == "Dark Elixir Barrack")
            self.assertEqual(troop.ground_target, troop_data.get("GroundTargets"))
            max_level = 0
            for k, v in troop_data.items():
                if not isinstance(v, dict):
                    continue
                level = v.get("VisualLevel")
                if not level:
                    continue
                max_level = max(max_level, level)
                level_troop = self.client.get_troop(troop_name, level=level)
                self.assertEqual(level_troop.name, troop_name, f"{level_troop.name} name is wrong")
                total_seconds = 0
                total_seconds += v.get("UpgradeTimeD", 0) * 24 * 60 * 60
                total_seconds += v.get("UpgradeTimeH", 0) * 60 * 60
                total_seconds += v.get("UpgradeTimeM", 0) * 60
                total_seconds += v.get("UpgradeTimeS", 0)
                self.assertEqual(level_troop.upgrade_cost or 0,
                                 v.get("UpgradeCost", 0) or 0,
                                 f"{level_troop.name} upgrade cost level {level} is wrong")
                self.assertEqual(level_troop.upgrade_time.total_seconds(), total_seconds,
                                 f"{level_troop.name} upgrade time level {level} is wrong")
            self.assertEqual(troop.max_level, max_level, f"{troop.name} max level is wrong")

import unittest

import coc

from coc.utils import UnitStatList


class ClashMetaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = coc.login_with_keys("")

    # def test_load_never(self):
    #     client = coc.login_with_keys("", load_game_data=coc.LoadGameData(never=True))
    #     with self.assertRaises(RuntimeError) as cm:
    #         client.parse_army_link("")
    #
    #     self.assertEqual(str(cm.exception), "Troop and Spell game metadata must be loaded to use this feature.")

    def test_load_default(self):
        client = coc.login_with_keys("", load_game_data=coc.LoadGameData(default=True))

        for holder in (client._troop_holder, client._spell_holder, client._hero_holder, client._pet_holder):
            self.assertTrue(holder.loaded)

    def test_load_startup_only(self):
        client = coc.login_with_keys("", load_game_data=coc.LoadGameData(startup_only=True))

        for holder in (client._troop_holder, client._spell_holder, client._hero_holder, client._pet_holder):
            self.assertTrue(holder.loaded)

        troop = client.get_troop("Barbarian")
        self.assertIs(type(troop), type(coc.Troop))

    def test_troop(self):
        barb = self.client.get_troop("Barbarian")
        self.assertIs(type(barb), type(coc.Troop))

        self.assertEqual(barb.name, "Barbarian")
        self.assertIsInstance(barb.level, UnitStatList)


class TroopMeta(unittest.TestCase):
    def setUp(self) -> None:
        self.client = coc.login_with_keys("")
        self.troop = self.client.get_troop("Barbarian")
        # self.barb_i = self.client.get_troop("Barbarian", level=12)

    def test_types(self):
        self.assertIs(type(self.troop), type(coc.Troop))

    def test_levels(self):
        self.assertIsInstance(self.troop.level, UnitStatList)

        with self.assertRaises(IndexError):
            self.troop.level[0]

        self.assertEqual(len(self.troop.level), len(self.troop.lab_level))
        print(self.troop.level, self.troop.dps)


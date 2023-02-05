import asyncio
import unittest
import os
import coc

# Siege data was grabbed from:
# https://clashofclans.fandom.com/wiki/Workshop
MACHINES = {
    "Siege Barracks":
        {
            "release": 13,
            "max_release_level": 4,
            "max_at": [
                {
                    "th": 13,
                    "max": 4
                }
            ]
        },
    "Wall Wrecker":
        {
            "release": 12,
            "max_release_level": 3,
            "max_at": [
                {
                    "th": 13,
                    "max": 4
                }
            ]
        },

}


class TestTroopLevel(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.coc_client = coc.Client()
        self.coc_client._create_holders()
        self.machines = MACHINES

    def test_siege_machines(self):
        for machine_key in self.machines.keys():
            machine = self.machines.get(machine_key)

            machine_obj = self.coc_client.get_troop(
                name=machine_key,
                townhall=machine.get("release"))
            max_level = machine_obj.get_max_level_for_townhall(12)
            self.assertEqual(None if 12 < machine.get('release') else machine.get('max_release_level'), max_level)


if __name__ == '__main__':
    unittest.main()

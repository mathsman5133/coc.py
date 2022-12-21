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
        self.machines = MACHINES

    async def asyncSetUp(self) -> None:
        await asyncio.sleep(1)
        try:
            await self.coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                                    os.environ.get(
                                        "DEV_SITE_PASSWORD"))
        except Exception as error:
            self.fail(msg=error)

    async def asyncTearDown(self) -> None:
        await self.coc_client.close()

    def test_siege_machines(self):
        for machine_key in self.machines.keys():
            machine = self.machines.get(machine_key)

            machine_obj = self.coc_client.get_troop(
                name=machine_key,
                townhall=machine.get("release") - 1)

            self.assertEqual(0, machine_obj.get_max_level_for_townhall(12))


if __name__ == '__main__':
    unittest.main()

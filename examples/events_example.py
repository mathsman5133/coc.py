import asyncio
import logging
import os

import coc
from coc import utils

clan_tags = ["#P222C9Y", "#9VPR98RG", "#9G2QU8YG", "#80Y8L0QY", "#2Y28CGP8"]

"""Clan Events"""


@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    log.info(
        f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")


@coc.ClanEvents.member_received()
async def on_clan_member_donation_receive(old_member, new_member):
    final_received_troops = new_member.received - old_member.received
    log.info(
        f"{new_member} of {new_member.clan} just received {final_received_troops} troops.")


@coc.ClanEvents.member_join()
async def on_clan_member_join(member, clan):
    log.info(f"{member.name} has joined {clan.name}")


@coc.ClanEvents.member_leave()
async def on_clan_member_leave(member, clan):
    log.info(f"{member.name} has left {clan.name}")


@coc.ClanEvents.points()
async def on_clan_trophy_change(old_clan, new_clan):
    log.info(
        f"{new_clan.name} total trophies changed from {old_clan.points} to {new_clan.points}")


@coc.ClanEvents.member_builder_base_trophies()
async def clan_member_builder_base_trophies_changed(old_member, new_member):
    log.info(
        f"{new_member} builder_base trophies changed from {old_member.builder_base_trophies} to"
        f" {new_member.builder_base_trophies}")


"""War Events"""


@coc.WarEvents.war_attack()
async def current_war_stats(attack, war):
    log.info(
        f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "
        f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")


@coc.WarEvents.new_war()
async def new_war(war):
    log.info(f"New war against {war.opponent.name} detected.")


"""Player Events"""


@coc.PlayerEvents.donations()
async def on_player_donation(old_player, new_player):
    final_donated_troops = new_player.donations - old_player.donations
    log.info(
        f"{new_player} of {new_player.clan} just donated {final_donated_troops} troops.")


@coc.PlayerEvents.received()
async def on_player_donation_receive(old_player, new_player):
    final_received_troops = new_player.received - old_player.received
    log.info(
        f"{new_player} of {new_player.clan} just received {final_received_troops} troops.")


@coc.PlayerEvents.trophies()
async def on_player_trophy_change(old_player, new_player):
    log.info(
        f"{new_player} trophies changed from {old_player.trophies} to {new_player.trophies}")


@coc.PlayerEvents.builder_base_trophies()
async def on_player_builder_base_trophy_change(old_player, new_player):
    log.info(
        f"{new_player} builder_base trophies changed from {old_player.builder_base_trophies} to {new_player.builder_base_trophies}")


"""Client Events"""


@coc.ClientEvents.maintenance_start()
async def on_maintenance():
    log.info("Maintenace Started")


@coc.ClientEvents.maintenance_completion()
async def on_maintenance_completion(time_started):
    log.info(f"Maintenace Ended; started at {time_started}")


@coc.ClientEvents.new_season_start()
async def season_started():
    log.info(f"New season started, and will finish at {str(utils.get_season_end())}")


@coc.ClientEvents.clan_games_end()
async def clan_games_ended():
    log.info(f"Clan games have ended. The next ones will start at {str(utils.get_clan_games_start())}")


@coc.ClientEvents.raid_weekend_start()
async def raid_weekend_started():
    log.info(f"A new Raid Weekend started. It will last until {str(utils.get_raid_weekend_end())}")


async def main() -> None:
    coc_client = coc.EventsClient()

    # Attempt to log into CoC API using your credentials. You must use the
    # coc.EventsClient to enable event listening
    try:
        await coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                               os.environ.get("DEV_SITE_PASSWORD"))
    except coc.InvalidCredentials as error:
        exit(error)

    # Register all the clans you want to track
    coc_client.add_clan_updates(*clan_tags)

    # Register all the players you want to track
    async for clan in coc_client.get_clans(clan_tags):
        coc_client.add_player_updates(*[member.tag for member in clan.members])

    # Register all the callback functions that are triggered when a
    # event if fired.
    coc_client.add_events(
        on_clan_member_donation,
        on_clan_member_donation_receive,
        on_clan_member_join,
        on_clan_member_leave,
        on_clan_trophy_change,
        clan_member_builder_base_trophies_changed,
        current_war_stats,
        on_player_donation,
        on_player_donation_receive,
        on_player_trophy_change,
        on_player_builder_base_trophy_change,
        on_maintenance,
        on_maintenance_completion,
        season_started
    )

    if os.environ.get("RUNNING_TESTS"):
        # ignore this; it's just for running github action tests.
        import sys

        class Handler(logging.Handler):
            def emit(self, record) -> None:
                sys.exit(0)

        log.addHandler(Handler())
        # we don't want to wait forever for an event, so if
        # it sets up OK lets call it quits.
        await asyncio.sleep(20)
        _loop = asyncio.get_event_loop()
        _loop.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger()

    # Unlike the other examples that use `asyncio.run()`, in order to run
    # events forever you must set the event loop to run forever so we will use
    # the lower level function calls to handle this.
    loop = asyncio.get_event_loop()

    try:
        # Using the loop context, run the main function then set the loop
        # to run forever so that it continuously monitors for events
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass

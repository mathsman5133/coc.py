import logging
import os

try:
    import coc
except ModuleNotFoundError:
    from .. import coc

client = coc.login(
    os.environ["DEV_SITE_EMAIL"],
    os.environ["DEV_SITE_PASSWORD"],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


clan_tags = ["#20090C9PR", "#202GG92Q", "#20C8G0RPL", "#20CG8UURL", "#20L2GVUCQ"]
player_tags = ["#YQ2QYLGJ", "#QYJCVGL", "#2LURLC9V", "#QCQR298V", "#82CVC2V8", "#29U09V8J", "#8GYGL22P"]


"""Clan Events"""


@client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations(tags=clan_tags)
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    log.info(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.ClanEvents.member_received(tags=clan_tags)
async def on_clan_member_donation_receive(old_member, new_member):
    final_received_troops = old_member.received - new_member.received
    log.info(f"{new_member} of {new_member.clan} just received {final_received_troops} troops.")


@client.event
@coc.ClanEvents.member_join(tags=clan_tags)
async def on_clan_member_join(member, clan):
    log.info(f"{member.name} has joined {clan.name}")


@client.event
@coc.ClanEvents.member_leave(tags=clan_tags)
async def on_clan_member_leave(member, clan):
    log.info(f"{member.name} has left {clan.name}")


@client.event
@coc.ClanEvents.points(tags=clan_tags)
async def on_clan_trophy_change(old_clan, new_clan):
    log.info(f"{new_clan.name} total trophies changed from {old_clan.points} to {new_clan.points}")


@client.event
@coc.ClanEvents.member_versus_trophies(tags=clan_tags)
async def clan_member_versus_trophies_changed(old_member, new_member):
    log.info(f"{new_member} versus trophies changed from {old_member.versus_trophies} to {new_member.versus_trophies}")


"""War Events"""


@client.event
@coc.WarEvents.war_attack(clan_tags, retry_interval=30)
async def current_war_stats(attack, war):
    log.info(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "
          f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")


"""Player Events"""


@client.event
@coc.PlayerEvents.donations(tags=player_tags)
async def on_player_donation(old_player, new_player):
    final_donated_troops = new_player.donations - old_player.donations
    log.info(f"{new_player} of {new_player.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.PlayerEvents.received(tags=player_tags)
async def on_player_donation_receive(old_player, new_player):
    final_received_troops = new_player.received - old_player.received
    log.info(f"{new_player} of {new_player.clan} just received {final_received_troops} troops.")


@client.event
@coc.PlayerEvents.trophies(tags=player_tags)
async def on_player_trophy_change(old_player, new_player):
    log.info(f"{new_player} trophies changed from {old_player.trophies} to {new_player.trophies}")


@client.event
@coc.PlayerEvents.versus_trophies(tags=player_tags)
async def on_player_versus_trophy_change(old_player, new_player):
    log.info(f"{new_player} versus trophies changed from {old_player.trophies} to {new_player.trophies}")


"""Client Events"""


@client.event
@coc.ClientEvents.maintenance_start()
async def on_maintenance():
    log.info("Maintenace Started")


@client.event
@coc.ClientEvents.maintenance_completion()
async def on_maintenance_completion(time_started):
    log.info("Maintenace Ended; started at %s", time_started)


if os.environ.get("RUNNING_TESTS"):
    # ignore this; it's just for running github action tests.
    import sys

    class Handler(logging.Handler):
        def emit(self, record) -> None:
            sys.exit(0)
    log.addHandler(Handler())

client.loop.run_forever()

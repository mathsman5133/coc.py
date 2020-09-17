import coc
import logging


client = coc.login(email="DevSiteEmail", password="DevSitePassword", client=coc.EventsClient)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


clan_tags = [
    "#20090C9PR",
    "#202GG92Q",
    "#20C8G0RPL",
    "#20CG8UURL",
    "#20L2GVUCQ",
]

player_tags = [
    "#YQ2QYLGJ",
    "#QYJCVGL",
    "#2LURLC9V",
    "#QCQR298V",
    "#82CVC2V8",
    "#29U09V8J",
    "#8GYGL22P",
]


"""Clan Events"""


@client.event  # Pro Tip : client event is mandatory then only any event will work so dont leave :)
@coc.ClanEvents.member_donations(tags=clan_tags)
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_donation.donations - old_donation.donations
    print(f"{new_donation} of {new_donation.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.ClanEvents.member_received(tags=clan_tags)
async def on_clan_member_donation_receive(new_received, old_received):
    final_received_troops = old_received.received - new_received.received
    print(f"{new_received} of {new_received.clan} just received {final_received_troops} troops.")


@client.event
@coc.ClanEvents.member_join(clan_tags, retry_interval=20)
async def on_clan_member_join(member, clan):
    print(f"{member.name} has joined {clan.name}")


@client.event
@coc.ClanEvents.member_leave(clan_tags, retry_interval=20)
async def on_clan_member_leave(member, clan):
    print(f"{member.name} has left {clan.name}")


@client.event
@coc.ClanEvents.points(clan_tags, retry_interval=10)
async def on_clan_trophy_change(old, new):
    print(f"{new.name} total trophies changed from {old.points} to {new.points}")


@client.event
@coc.ClanEvents.member_versus_trophies(clan_tags, retry_interval=10)
async def clan_member_versus_trophies_changed(old_member, new_member):
    print(f"{new.name} total versus trophies changed from {old.versus_trophies} to {new.versus_trophies}")


"""War Events"""


@client.event
@coc.WarEvents.war_attack(clan_tags, retry_interval=30)
async def current_war_stats(attack, war):
    print(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")


"""Player Events"""


@client.event
@coc.PlayerEvents.donations(tags=player_tags)
async def on_player_donation(old_donation, new_donation):
    final_donated_troops = new_donation.donations - old_donation.donations
    print(f"{new_donation} of {new_donation.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.PlayerEvents.received(tags=player_tags)
async def on_player_donation_receive(new_received, old_received):
    final_received_troops = old_received.received - new_received.received
    print(f"{new_received} of {new_received.clan} just received {final_received_troops} troops.")


@client.event
@coc.PlayerEvents.trophies(tags=player_tags)
async def on_player_trophy_change(old, new):
    print(f"{new} trophies changed from {old.trophies} to {new.trophies}")


@client.event
@coc.PlayerEvents.versus_trophies(tags=player_tags)
async def on_player_versus_trophy_change(old, new):
    print(f"{new} versus trophies changed from {old.trophies} to {new.trophies}")


"""Client Events"""


@client.event
@coc.ClientEvents.maintenance_start()
async def on_maintenance():
    log.info("Maintenace Started")


@client.event
@coc.ClientEvents.maintenance_completion()
async def on_maintenance_completion():
    log.info("Maintenace Ended")


client.loop.run_forever()

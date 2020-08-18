import coc
import logging
import asyncio
import objgraph
import psutil
import tracemalloc
import random


tracemalloc.start()

client = coc.login('emailOfdevsite', 'passwordOfDevsite', client=coc.EventsClient, key_names="windows", cwl_active=False)
log = logging.getLogger()
logging.basicConfig(level=logging.CRITICAL)

c_tags = [
    "#20090C9PR",
    "#202GG92Q",
    "#20C8G0RPL",
    "#20CG8UURL",
    "#20L2GVUCQ",
    "#20PJQQP0G",
    "#20RP90PLL",
    "#20VCVGVCG",
    "#20YRUQRLJ",
    "#2229Y88R9",
    "#228VP82GY",
    "#22GLCR9Q",
    "#22J8ULLL",
    "#22JYYGVUC",
    "#22LR9QY98",
    "#22PQL2L0R",
    "#22QCGYV2Q",
    "#22RGGJVP",
    "#22RU00UC9",
    "#22YCYL89",
    "#22YRJLVU8",
    "#280V0VYL",
    "#282L8GLJ",
    "#28CJ8RRYJ",
    "#28GCGPVL2",
    "#28GQ08L29",
    "#28Q0R2QV9",
    "#28QJ2LP8Q",
    "#28QLCPCLG",
    "#28QRV0Y0G",
    "#28ULR99VL",
    "#28V2RC0C9",
    "#28VPCGV2G",
    "#28VQUV9J8",
    "#28YC02QYC",
    "#290UJUQVQ",
    "#2922CY2R",
    "#292GVY28P",
    "#2982PCG09",
    "#298CJ9JPC",
    "#2998PGPY9",
    "#29998R8L0",
    "#299C8QR9L",
    "#299P28QRL",
    "#29CV8VLL2",
    "#29G2JU888",
    "#29G9QJVLR",
    "#29GC8JQG0",
    "#29GLJCLQQ",
    "#29GLLLURV",
    "#29GQCC29C",
    "#29GQQ9GVL",
    "#29GVQV9Q9",
    "#29GVYYJ8",
    "#29L00JCVG",
    "#29L2U9U9J",
    "#29LPUGR9L",
    "#29LPVL99P",
    "#29LUPU9QV",
    "#29PJYUCV2",
    "#29RY29LL2",
    "#29U9UYUG",
    "#29VC9GR0Y",
    "#29Y2QVGL",
    "#29Y2R0CJQ",
    "#2C8JV0PG",
    "#2CR80PVR",
    "#2CVLP0P0",
    "#2G2LR0",
    "#2G9C9CVC",
    "#2GU2Y0JL",
    "#2JU0P82U",
    "#2JUJ2G22",
    "#2LP2PUUP",
    "#2P0C9LY8Y",
    "#2P0QL9C9G",
    "#2P2JR088R",
    "#2P2LJJPUY",
    "#2P2Q9PPJJ",
    "#2P2UVPRVC",
    "#2P80Q9LR8",
    "#2P89GGLYY",
    "#2P9CGUUR8",
    "#2P9PC0JC9",
    "#2PCUQJYGJ",
    "#2PG8R9GU8",
    "#2PGJUL98L",
    "#2PGQY2YPV",
    "#2PGV2GUUJ",
    "#2PJJPGJ9U",
    "#2PLGGYGLV",
    "#2PLLQRQPP",
    "#2PLR9VPYP",
    "#2PPR9VUGC",
    "#2PQ08LCGR",
    "#2PQY9GQU9",
    "#2PRPJU8RY",
    "#2PUGC20UC",
    "#2PUL8RU82",
    "#2PUPY9022",
    "#P99CRYU2",
]

@client.event #Pro Tip : client event is mandatory then only any event will work so dont leave :)
@coc.ClanEvents.member_donations(tags=c_tags)
async def on_clan_member_donation(old_player, new_player):
    new_donations = new_player.donations - old_player.donations
    print(f"{new_player} of {new_player.clan} just donated {new_donations} troops.")

@client.event 
@coc.ClanEvents.member_received(tags=c_tags)
async def on_clan_member_receive(old_player, new_player):
    new_received = new_player.received - old_player.received
    print(f"{new_player} of {new_player.clan} just received {new_received} troops.")


@coc.WarEvents.war_attack(tags=c_tags)
async def test():
    pass


@coc.WarEvents.war_attack()
async def test():
    pass


@coc.WarEvents.war_attack()
async def callable():
    pass


@client.event
@coc.WarEvents.war_attack(c_tags, retry_interval=30)
async def change2(attack, new):
    print(f'Attack number {max(a.order for a in new.attacks)}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}')


@client.event
@coc.ClanEvents.points(c_tags, retry_interval=0)
async def on_clan_trophy_change(old, new):
    print(f'{new.name} total trophies changed from {old.points} to {new.points}')


async def on_maintenance():
    log.critical("maintenance start")


async def on_maintenance_completion(start_time):
    log.critical("maintenance finished")


client.on_maintenance = on_maintenance
client.on_maintenance_completion = on_maintenance_completion


# async def get_lots_of_playertags():
#     new_tags = []
#     for _ in range(3):
#         try:
#             await client.get_clan("#abc123")
#         except:
#             pass
#     async for clan in client.get_clans(c_tags):
#         print(clan)
#         new_tags.extend(n.tag for n in clan.members)
#     return new_tags


# tags = client.loop.run_until_complete(get_lots_of_playertags())
# log.info(str(tags) + ",,")
# client.add_player_updates(tags)


async def task():
    process = psutil.Process()
    for i in range(500):
        memory = process.memory_full_info().uss / 1024 ** 2
        print(f"Memory At {i} round: {memory:.2f} MiB")
        objgraph.show_growth()
        objgraph.show_most_common_types()
        # roots = objgraph.get_leaking_objects()
        # objgraph.show_refs(roots[:3], refcounts=True, filename=f"~graphs/chain{i}.png")
        # objgraph.show_most_common_types(objects=roots)
        # chain = objgraph.find_backref_chain(objgraph.by_type('cell')[-1], inspect.ismodule)
        # in_chain = lambda x, ids=set(map(id, chain)): id(x) in ids
        # objgraph.show_backrefs(chain[-1], len(chain), filter=in_chain, filename=f"~graphs/chain{i}.png")
        # objgraph.show_backrefs(
        #     random.choice(objgraph.by_type("cell")),
        #     filename=f"~graphs/chain{i}.png"
        # )
        # objgraph.show_chain(objgraph.find_backref_chain(
        #     random.choice(objgraph.by_type("cell")),
        #     objgraph.is_proper_module
        # ),
        #     filename=f"~graphs/chain{i}.png"
        # )

        # Wait a few seconds
        await asyncio.sleep(120)


loop = asyncio.get_event_loop()
loop.create_task(task())
client.loop.run_forever()

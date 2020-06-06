import coc
import logging
import asyncio
import objgraph
import psutil


client = coc.login("mathsman5132@gmail.com", "creepy_crawley", client=coc.EventsClient, key_names="windows")
log = logging.getLogger()


@client.event
@coc.ClanEvents.member_donations_change(["#8QR8VRP8", "#PRUJU08V", "#CQ29CCU", "#LLRJJP02"], retry_interval=5)
async def on_player_trophies_change(member, clan):
    print("player trophies change ran properly!")


async def task():
    process = psutil.Process()
    for i in range(500):
        memory = process.memory_full_info().uss / 1024 ** 2
        print(f"Memory At {i} round: {memory:.2f} MiB")
        objgraph.show_growth()

        # Wait a few seconds
        await asyncio.sleep(60)


client.loop.create_task(task())
client.run_forever()

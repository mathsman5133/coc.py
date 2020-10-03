# this example assumes you have discord.py > v1.5
# installed via `python -m pip install -U discord.py`
# for more info on using discord.py, see the docs at:
# https://discordpy.readthedocs.io/en/latest

import logging
import os
import traceback

import coc
import discord

from coc import utils
from discord.ext import commands


INFO_CHANNEL_ID = 761848043242127370  # some discord channel ID
clan_tags = ["#20090C9PR", "#202GG92Q", "#20C8G0RPL"]

bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
coc_client = coc.login(
    os.environ["DEV_SITE_EMAIL"],
    os.environ["DEV_SITE_PASSWORD"],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.ERROR)


@coc_client.event
@coc.ClanEvents.member_join(tags=clan_tags)
async def on_clan_member_join(member, clan):
    await bot.get_channel(INFO_CHANNEL_ID).send(
        "{0.name} ({0.tag}) just " "joined our clan {1.name} ({1.tag})!".format(member, clan)
    )


@coc_client.event
@coc.ClanEvents.member_name(tags=clan_tags)
async def member_name_change(old_player, new_player):
    await bot.get_channel(INFO_CHANNEL_ID).send(
        "Name Change! {0.name} is now called {1.name} (his tag is {1.tag})".format(old_player, new_player)
    )


@coc_client.event
@coc.ClientEvents.event_error()
async def on_event_error(exception):
    if isinstance(exception, coc.PrivateWarLog):
        return  # lets ignore private war log errors
    print("Uh oh! Something went wrong in coc.py events... printing traceback for you.")
    traceback.print_exc()


@bot.command()
async def player_heroes(ctx, player_tag):
    if not utils.is_valid_tag(player_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        player = await coc_client.get_player(player_tag)
    except coc.NotFound:
        await ctx.send("This player doesn't exist!")
        return
        
    to_send = ""
    for hero in player.heroes:
        to_send += "{}: Lv{}/{}\n".format(str(hero), hero.level, hero.max_level)

    await ctx.send(to_send)


@bot.command()
async def clan_info(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        clan = await coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan doesn't exist!")
        return
        
    if clan.public_war_log is False:
        log = "Private"
    else:
        log = "Public"

    e = discord.Embed(colour=discord.Colour.green())
    e.set_thumbnail(url=clan.badge.url)
    e.add_field(name="Clan Name", value=f"{clan.name}({clan.tag})\n[Open in game]({clan.share_link})", inline=False)
    e.add_field(name="Clan Level", value=clan.level, inline=False)
    e.add_field(name="Description", value=clan.description, inline=False)
    e.add_field(name="Leader", value=clan.get_member_by(role=coc.Role.leader), inline=False)
    e.add_field(name="Clan Type", value=clan.type, inline=False)
    e.add_field(name="Location", value=clan.location, inline=False)
    e.add_field(name="Total Clan Trophies", value=clan.points, inline=False)
    e.add_field(name="Total Clan Versus Trophies", value=clan.versus_points, inline=False)
    e.add_field(name="WarLog Type", value=log, inline=False)
    e.add_field(name="Required Trophies", value=clan.required_trophies, inline=False)
    e.add_field(name="War Win Streak", value=clan.war_win_streak, inline=False)
    e.add_field(name="War Frequency", value=clan.war_frequency, inline=False)
    e.add_field(name="Clan War League Rank", value=clan.war_league, inline=False)
    e.add_field(name="Clan Labels", value="\n".join(label.name for label in clan.labels), inline=False)
    e.add_field(name="Member Count", value=f"{clan.member_count}/50", inline=False)
    e.add_field(
        name="Clan Record",
        value=f"Won - {clan.war_wins}\nLost - {clan.war_losses}\n Draw - {clan.war_ties}",
        inline=False
    )
    await ctx.send(embed=e)


@bot.command()
async def clan_member(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        clan = await coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan does not exist!")
        return
        
    member = ""
    for i, a in enumerate(clan.members, start=1):
        member += f"`{i}.` {a.name}\n"
    embed = discord.Embed(colour=discord.Colour.red(), title=f"Members of {clan.name}", description=member)
    embed.set_thumbnail(url=clan.badge.url)
    embed.set_footer(text=f"Total Members - {clan.member_count}/50")
    await ctx.send(embed=embed)


@bot.command()
async def current_war_status(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    e = discord.Embed(colour=discord.Colour.blue())

    try:
        war = await coc_client.get_current_war(clan_tag)
    except coc.PrivateWarLog:
        return await ctx.send("Clan has a private war log!")

    if war is None:
        return await ctx.send("Clan is in a strange CWL state!")

    e.add_field(name="War State:", value=war.state, inline=False)

    if war.end_time:  # if state is notInWar we will get errors

        hours, remainder = divmod(int(war.end_time.seconds_until), 3600)
        minutes, seconds = divmod(remainder, 60)

        e.add_field(name=war.clan.name, value=war.clan.tag)
        e.add_field(name="Opponent:", value=f"{war.opponent.name}\n" f"{war.opponent.tag}", inline=False)
        e.add_field(name="War End Time:", value=f"{hours} hours {minutes} minutes {seconds} seconds", inline=False)

    await ctx.send(embed=e)


async def run_tests_and_quit():
    # ignore this; it is purely for the benefit of being able to run the examples as tests.
    import sys

    class Msg:
        _state = bot._connection

    await bot.wait_until_ready()
    ctx = commands.Context(prefix=None, message=Msg, bot=bot)

    async def _mock_get_channel():
        return bot.get_channel(INFO_CHANNEL_ID)
    ctx._get_channel = _mock_get_channel

    await ctx.invoke(player_heroes, "#JY9J2Y99")
    for command in (clan_info, clan_member, current_war_status):
        await ctx.invoke(command, clan_tags[0])

    sys.exit(0)

if os.environ.get("RUNNING_TESTS"):
    bot.loop.create_task(run_tests_and_quit())

bot.run(os.environ["DISCORD_BOT_TOKEN"])

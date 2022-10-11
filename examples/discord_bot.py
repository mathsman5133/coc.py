# this example assumes you have discord.py > v2.0
# installed via `python -m pip install -U discord.py`
# for more info on using discord.py, see the docs at:
# https://discordpy.readthedocs.io/en/latest
import asyncio
import logging
import os
import traceback

import discord
from discord.ext import commands

import coc
from coc import utils

INFO_CHANNEL_ID = 761848043242127370  # some discord channel ID
clan_tags = ["#20090C9PR", "#202GG92Q", "#20C8G0RPL"]

bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("Logged in!!")


@coc.ClanEvents.member_join(tags=clan_tags)
async def on_clan_member_join(member, clan):
    await bot.get_channel(INFO_CHANNEL_ID).send(
        "{0.name} ({0.tag}) just " "joined our clan {1.name} ({1.tag})!".format(
            member, clan)
    )


@coc.ClanEvents.member_name(tags=clan_tags)
async def member_name_change(old_player, new_player):
    await bot.get_channel(INFO_CHANNEL_ID).send(
        "Name Change! {0.name} is now called {1.name} (his tag is {1.tag})".format(
            old_player, new_player)
    )


@coc.ClientEvents.event_error()
async def on_event_error(exception):
    if isinstance(exception, coc.PrivateWarLog):
        return  # lets ignore private war log errors
    print(
        "Uh oh! Something went wrong in coc.py events... printing traceback for you.")
    traceback.print_exc()


@bot.command()
async def player_heroes(ctx, player_tag):
    if not utils.is_valid_tag(player_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        player = await ctx.bot.coc_client.get_player(player_tag)
    except coc.NotFound:
        await ctx.send("This player doesn't exist!")
        return

    to_send = ""
    for hero in player.heroes:
        to_send += "{}: Lv{}/{}\n".format(str(hero),
                                          hero.level, hero.max_level)

    await ctx.send(to_send)


@bot.command()
async def parse_army(ctx, army_link: str):
    troops, spells = ctx.bot.coc_client.parse_army_link(army_link)
    print(troops, spells)
    parsed_link_output = ''
    if troops or spells:  # checking if troops or spells is present in link

        for troop, quantity in troops:
            parsed_link_output += "The user wants {} {}s. They each have {} DPS.\n".format(
                quantity, troop.name, troop.dps)

        for spell, quantity in spells:
            parsed_link_output += "The user wants {} {}s.\n".format(
                quantity, spell.name)
    else:
        parsed_link_output += "Invalid Link!"
    await ctx.send(parsed_link_output)


@bot.command()
async def create_army(ctx):
    link = ctx.bot.coc_client.create_army_link(
        barbarian=10,
        archer=20,
        hog_rider=30,
        healing_spell=3,
        poison_spell=2,
        rage_spell=2
    )
    await ctx.send(link)


@bot.command()
async def member_stat(ctx, player_tag):
    if not utils.is_valid_tag(player_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        player = await ctx.bot.coc_client.get_player(player_tag)
    except coc.NotFound:
        await ctx.send("This clan doesn't exist!")
        return

    frame = ''
    if player.town_hall > 11:
        frame += f"`{'TH Weapon LvL:':<15}` `{player.town_hall_weapon:<15}`\n"
    role = player.role if player.role else 'None'
    clan = player.clan.name if player.clan else 'None'
    frame += (
        f"`{'Role:':<15}` `{role:<15}`\n"
        f"`{'Player Tag:':<15}` `{player.tag:<15}`\n"
        f"`{'Current Clan:':<15}` `{clan:<15.15}`\n"
        f"`{'League:':<15}` `{player.league.name:<15.15}`\n"
        f"`{'Trophies:':<15}` `{player.trophies:<15}`\n"
        f"`{'Best Trophies:':<15}` `{player.best_trophies:<15}`\n"
        f"`{'War Stars:':<15}` `{player.war_stars:<15}`\n"
        f"`{'Attack Wins:':<15}` `{player.attack_wins:<15}`\n"
        f"`{'Defense Wins:':<15}` `{player.defense_wins:<15}`\n"
        f"`{'Castle Contrib':<15}` `{player.clan_capital_contributions:<15}`\n"
    )
    e = discord.Embed(colour=discord.Colour.green(),
                      description=frame)
    e.set_thumbnail(url=player.clan.badge.url)
    await ctx.send(embed=e)


@bot.command()
async def clan_info(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        clan = await ctx.bot.coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan doesn't exist!")
        return

    if clan.public_war_log is False:
        log = "Private"
    else:
        log = "Public"

    e = discord.Embed(colour=discord.Colour.green())

    e.set_thumbnail(url=clan.badge.url)
    e.add_field(name="Clan Name",
                value=f"{clan.name}({clan.tag})\n[Open in game]({clan.share_link})",
                inline=False)
    e.add_field(name="Clan Level", value=clan.level, inline=False)
    e.add_field(name="Description", value=clan.description, inline=False)
    e.add_field(name="Leader", value=clan.get_member_by(
        role=coc.Role.leader), inline=False)
    e.add_field(name="Clan Type", value=clan.type, inline=False)
    e.add_field(name="Location", value=clan.location, inline=False)
    e.add_field(name="Total Clan Trophies", value=clan.points, inline=False)
    e.add_field(name="Total Clan Versus Trophies",
                value=clan.versus_points, inline=False)
    e.add_field(name="WarLog Type", value=log, inline=False)
    e.add_field(name="Required Trophies",
                value=clan.required_trophies, inline=False)
    e.add_field(name="War Win Streak", value=clan.war_win_streak, inline=False)
    e.add_field(name="War Frequency", value=clan.war_frequency, inline=False)
    e.add_field(name="Clan War League Rank",
                value=clan.war_league, inline=False)
    e.add_field(name="Clan Labels", value="\n".join(
        label.name for label in clan.labels), inline=False)
    e.add_field(name="Member Count",
                value=f"{clan.member_count}/50", inline=False)
    e.add_field(
        name="Clan Record",
        value=f"Won - {clan.war_wins}\nLost - {clan.war_losses}\n Draw - {clan.war_ties}",
        inline=False
    )

    frame = ""
    for district in clan.capital_districts:
        frame += (f"`{f'{district.name}:':<20}` `{district.hall_level:<15}`\n")

    e2 = discord.Embed(colour=discord.Colour.green(), description=frame,
                       title="Capital Distracts")

    await ctx.send(embeds=[e, e2])


@bot.command()
async def clan_member(ctx, clan_tag):
    if not utils.is_valid_tag(clan_tag):
        await ctx.send("You didn't give me a proper tag!")
        return

    try:
        clan = await ctx.bot.coc_client.get_clan(clan_tag)
    except coc.NotFound:
        await ctx.send("This clan does not exist!")
        return

    member = ""
    for i, a in enumerate(clan.members, start=1):
        member += f"`{i}.` {a.name}\n"

    embed = discord.Embed(colour=discord.Colour.red(),
                          title=f"Members of {clan.name}", description=member)
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
        war = await ctx.bot.coc_client.get_current_war(clan_tag)
    except coc.PrivateWarLog:
        return await ctx.send("Clan has a private war log!")

    if war is None:
        return await ctx.send("Clan is in a strange CWL state!")

    e.add_field(name="War State:", value=war.state, inline=False)

    if war.end_time:  # if state is notInWar we will get errors

        hours, remainder = divmod(int(war.end_time.seconds_until), 3600)
        minutes, seconds = divmod(remainder, 60)

        e.add_field(name=war.clan.name, value=war.clan.tag)
        e.add_field(
            name="Opponent:",
            value=f"{war.opponent.name}\n" f"{war.opponent.tag}", inline=False)
        e.add_field(name="War End Time:",
                    value=f"{hours} hours {minutes} minutes {seconds} seconds",
                    inline=False)

    await ctx.send(embed=e)


async def main():
    logging.basicConfig(level=logging.ERROR)

    coc_client = coc.Client()

    # Attempt to log into CoC API using your credentials.
    try:
        await coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                               os.environ.get("DEV_SITE_PASSWORD"))
    except coc.InvalidCredentials as error:
        exit(error)

    # Add the client session to the bot
    bot.coc_client = coc_client

    try:
        # Run the bot
        await bot.start(os.environ.get("DISCORD_BOT_TOKEN"))
    finally:
        # When done, do not forget to clean up after yourself!
        await coc_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

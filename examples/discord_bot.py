# this example assumes you have discord.py > v1.0.0 installed via `python -m pip install -U discord.py`
# for more info on using discord.py, see the docs at: https://discordpy.readthedocs.io/en/latest/api.html#message
import discord
from discord.ext import commands

import coc

bot = commands.Bot(command_prefix='?')
coc_client = coc.Client('email', 'password', key_count=5, key_names='My funky name!')


@bot.command()
async def player_heroes(ctx, player_tag):
    player = await coc_client.get_player(player_tag)

    to_send = ''
    for hero in player.heroes:
        to_send += '{}: Lv{}/{}'.format(str(hero), hero.level, hero.max_level)

    await ctx.send(to_send)
    
    
@bot.command()
async def clan_info(ctx, clan_tag):
    clan = await coc_client.get_clan(clan_tag)
    
    e = discord.Embed(colour=discord.Colour.green())
    e.set_thumbnail(url=clan.badge.url)
    e.add_field(name=clan.name,
                value=clan.tag)
    e.add_field(name="Description",
                value=clan.description)
    e.add_field(name="Members",
                value=", ".join([member.name for member in clan.members]))
    e.add_field(name="Clan Record",
                value="{}-{}-{}".format(clan.war_wins, clan.war_losses, clan.war_ties))
    
    await ctx.send(embed=e)


@bot.command()
async def current_war_status(ctx, clan_tag):
    e = discord.Embed(colour=discord.Colour.blue())

    try:
        war = await coc_client.get_current_war(clan_tag)
    except coc.Forbidden:
        return await ctx.send('Clan has a private war log!')

    e.add_field(name=war.clan.name,
                value=war.clan.tag)

    e.add_field(name='War State:',
                value=war.state,
                inline=False)

    if war.end_time:  # if state is notInWar we will get errors

        hours, remainder = divmod(int(war.end_time.seconds_until), 3600)
        minutes, seconds = divmod(remainder, 60)

        e.add_field(name='Opponent:',
                    value=f"{war.opponent.name}\n"
                          f"{war.opponent.tag}",
                    inline=False)
        e.add_field(name="War End Time:",
                    value=f'{hours} hours {minutes} minutes {seconds} seconds',
                    inline=False)

    await ctx.send(embed=e)

bot.run('bot token')


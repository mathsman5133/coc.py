import asyncio
import os

import aiohttp
import discord
from discord.ext import commands

import coc

# Clan tags we want to listen for
clan_tags = ["#P222C9Y", "#9VPR98RG", "#9G2QU8YG", "#80Y8L0QY", "#2Y28CGP8"]


class CoCBot(commands.Bot):
    """Inherit from commands.Bot so that you can easily configure the bots
    behaviour"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coc_client: coc.EventsClient = kwargs.get("coc_client")

    async def on_ready(self):
        print("Logged in!!")

    async def setup_hook(self) -> None:
        # Add command cog class to start listening for those commands
        await self.add_cog(CocCommands(self))

        # Register your CoC Events
        self.coc_client.add_clan_updates(*clan_tags)

        # Register all the players you want to track
        async for clan in self.coc_client.get_clans(clan_tags):
            self.coc_client.add_player_updates(
                *[member.tag for member in clan.members])

        # Register the callback functions for the evens you are listening for
        self.coc_client.add_events(
            on_clan_member_donation,
            on_clan_member_donation_receive,
            on_clan_trophy_change,
        )


class CocCommands(commands.Cog):
    """This class holds the commands supported by the bot"""
    def __init__(self, bot: CoCBot):
        self.bot = bot

    @commands.command()
    async def member_stat(self, ctx, player_tag):
        if not coc.utils.is_valid_tag(player_tag):
            await ctx.send("You didn't give me a proper tag!")
            return

        try:
            player = await self.bot.coc_client.get_player(player_tag)
        except coc.NotFound:
            await ctx("This clan doesn't exist!")
            return

        print("Hello")
        try:
            for spell in player.spells:
                print(spell)
        except Exception as error:
            import traceback
            exc = ''.join(traceback.format_exception(type(error), error,
                                                     error.__traceback__,
                                                     chain=True))
            print(exc)

        frame = ""
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

    @commands.command()
    async def clan_info(self, ctx, clan_tag):
        if not coc.utils.is_valid_tag(clan_tag):
            await ctx.send("You didn't give me a proper tag!")
            return

        try:
            clan = await self.bot.coc_client.get_clan(clan_tag)
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

        e.add_field(name="Clan Level",
                    value=clan.level,
                    inline=False)

        e.add_field(name="Description",
                    value=clan.description,
                    inline=False)

        e.add_field(name="Leader",
                    value=clan.get_member_by(role=coc.Role.leader),
                    inline=False)

        e.add_field(name="Clan Type",
                    value=clan.type,
                    inline=False)

        e.add_field(name="Location",
                    value=clan.location,
                    inline=False)

        e.add_field(name="Total Clan Trophies",
                    value=clan.points,
                    inline=False)

        e.add_field(name="Total Clan Versus Trophies",
                    value=clan.versus_points,
                    inline=False)

        e.add_field(name="WarLog Type",
                    value=log,
                    inline=False)

        e.add_field(name="Required Trophies",
                    value=clan.required_trophies,
                    inline=False)

        e.add_field(name="War Win Streak",
                    value=clan.war_win_streak,
                    inline=False)

        e.add_field(name="War Frequency",
                    value=clan.war_frequency,
                    inline=False)

        e.add_field(name="Clan War League Rank",
                    value=clan.war_league,
                    inline=False)

        e.add_field(name="Clan Labels",
                    value="\n".join(label.name for label in clan.labels),
                    inline=False)

        e.add_field(name="Member Count",
                    value=f"{clan.member_count}/50",
                    inline=False)

        e.add_field(
            name="Clan Record",
            value=f"Won - {clan.war_wins}\nLost - {clan.war_losses}\n "
                  f"Draw - {clan.war_ties}",
            inline=False
        )

        frame = ""
        for district in clan.capital_districts:
            frame += (f"`{f'{district.name}:':<20}` "
                      f"`{district.hall_level:<15}`\n")

        e2 = discord.Embed(colour=discord.Colour.green(), description=frame,
                           title="Capital Distracts")

        await ctx.send(embeds=[e, e2])


async def send_via_webhook(msg: str) -> None:
    """Webhooks allow you to send messages to discord without having to
    have a bot session. Keep in mind that you need to create the webhook
    URL from Discord"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK")
    if webhook_url is None:
        print("No URL webhook found")
        return

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(os.environ.get("DISCORD_WEBHOOK"),
                                           session=session)
        await webhook.send(msg)


# The following decorators are listeners. Keep in mind that they must first
# be registered before they work. The registration process happens during
# the bots `setup_hook`
@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    msg =(f"{new_member} of {new_member.clan} just donated "
          f"{final_donated_troops} troops.")
    print(msg)
    await send_via_webhook(msg)


@coc.ClanEvents.member_received()
async def on_clan_member_donation_receive(old_member, new_member):
    final_received_troops = new_member.received - old_member.received
    msg = (f"{new_member} of {new_member.clan} just received "
           f"{final_received_troops} troops.")
    print(msg)
    await send_via_webhook(msg)


@coc.ClanEvents.points()
async def on_clan_trophy_change(old_clan, new_clan):
    msg =(f"{new_clan.name} total trophies changed from {old_clan.points} "
          f"to {new_clan.points}")
    print(msg)
    await send_via_webhook(msg)


async def main():
    coc_client = coc.EventsClient()

    # Attempt to log into CoC API using your credentials. To enable events,
    # you must use the coc.EventsClient class
    try:
        await coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                               os.environ.get("DEV_SITE_PASSWORD"))
    except coc.InvalidCredentials as error:
        exit(error)

    # Instantiate your custom bot class that inherits from the discord bot
    # notice that we added coc_client into the bot. This will give us access
    # to coc_client from all our discord bot commands
    bot = CoCBot(command_prefix="?",
                 intents=discord.Intents.all(),
                 coc_client=coc_client)

    try:
        # Run the bot
        await bot.start(os.environ.get("DISCORD_BOT_TOKEN"))
    finally:
        # When done, do not forget to clean up after yourself!
        await coc_client.close()


if __name__ == "__main__":
    try:
        # It is recommended to use the high level asyncio.run wrapper to
        # properly cleanup after the loops are done
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

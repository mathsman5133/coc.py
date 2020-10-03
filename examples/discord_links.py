import asyncio
import os

import coc

from coc.ext import discordlinks

client = discordlinks.login(os.environ["LINKS_API_USERNAME"], os.environ["LINKS_API_PASSWORD"])


async def main():
    player_tag = "#JY9J2Y99"
    discord_id = 230214242618441728

    # add a link
    await client.add_link(player_tag, discord_id)
    print("Player Tag {} is now linked to discord id {}".format(player_tag, discord_id))

    # get a link by tag
    discord_id = await client.get_link(player_tag)
    print("Player Tag {} is linked to discord id {}".format(player_tag, discord_id))

    # update a link
    new_discord_id = 230214242618441728
    await client.delete_link(player_tag)
    await client.add_link(player_tag, new_discord_id)
    print("Link for player tag {} has been updated to have discord id {}".format(player_tag, new_discord_id))

    # delete a link
    await client.delete_link(player_tag)
    print("Link for player tag {} has been removed from the database.".format(player_tag))

    # batch get links by tag
    player_tags = ["#JY9J2Y99", "#2GV0QY8G8", "#PP9L22C8", "#2LPC9J8L"]
    links = await client.get_links(*player_tags)
    for tag, discord_id in links:
        if discord_id is None:
            print("Player tag {} doesn't have any links.".format(tag))
        else:
            print("Player tag {} is linked to discord id {}".format(tag, discord_id))

    # batch get links by id
    discord_ids = [246286410946969610, 230214242618441728, 267057699856842753]
    links = await client.get_many_linked_players(*discord_ids)
    for tag, discord_id in links:
        print("Discord ID {} is linked to {}".format(tag, discord_id))


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

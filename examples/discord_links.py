import asyncio

from coc.ext import discordlinks

client = discordlinks.login("username", "password")


async def main():
    player_tag = "#ABC123"
    discord_id = 123456789

    # add a link
    await client.add_discord_link(player_tag, discord_id)
    print("Player Tag {} is now linked to discord id {}".format(player_tag, discord_id))

    # get a link by tag
    discord_id = await client.get_discord_link(player_tag)
    print("Player Tag {} is linked to discord id {}".format(player_tag, discord_id))

    # update a link
    new_discord_id = 12345678987654321
    await client.update_discord_link(player_tag, new_discord_id)
    print("Link for player tag {} has been updated to have discord id {}".format(player_tag, new_discord_id))

    # delete a link
    await client.delete_discord_link(player_tag)
    print("Link for player tag {} has been removed from the database.".format(player_tag))

    # batch get links by tag
    player_tags = ["#ABC123", "#123ABC", "#DEF456", "456DEF"]
    links = await client.get_discord_links(player_tags)
    for tag, discord_id in links.items():
        print("Player tag {} is linked to discord id {}".format(tag, discord_id))

    # batch get links by id
    discord_ids = [12345, 67890, 24680, 13579]
    links = await client.get_batch_discord_linked_players(discord_ids)
    for id_, tags in links.items():
        print("Discord ID {} has the following linked accounts: ".format(id_) + ", ".join(tags))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

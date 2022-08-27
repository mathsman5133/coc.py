import asyncio
import os

from coc.ext import discordlinks


async def main():
    client = await discordlinks.login(os.environ["LINKS_API_USERNAME"],
                                      os.environ["LINKS_API_PASSWORD"])

    player_tag = "#JY9J2Y99"
    discord_id = 230214242618441728

    # add a link
    await client.add_link(player_tag, discord_id)
    print(f"Player Tag {player_tag} is now linked to discord id {discord_id}")

    # get a link by tag
    discord_id = await client.get_link(player_tag)
    print(f"Player Tag {player_tag} is linked to discord id {discord_id}")

    # update a link
    new_discord_id = 230214242618441728
    await client.delete_link(player_tag)
    await client.add_link(player_tag, new_discord_id)
    print(f"Link for player tag {player_tag} has been updated to "
          f"have discord id {new_discord_id}")

    # delete a link
    await client.delete_link(player_tag)
    print(f"Link for player tag {player_tag} has been removed from "
          f"the database.")

    # batch get links by tag
    player_tags = ["#JY9J2Y99", "#2GV0QY8G8", "#PP9L22C8", "#2LPC9J8L"]
    links = await client.get_links(*player_tags)
    for tag, discord_id in links:
        if discord_id is None:
            print(f"Player tag {tag} doesn't have any links.")
        else:
            print(f"Player tag {tag} is linked to discord id {discord_id}")

    # batch get links by id
    discord_ids = [246286410946969610, 230214242618441728, 267057699856842753]
    links = await client.get_many_linked_players(*discord_ids)
    for tag, discord_id in links:
        print(f"Discord ID {tag} is linked to {discord_id}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

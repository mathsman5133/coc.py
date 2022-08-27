import asyncio
import os

import coc


async def get_warlog_for_clans(client: coc.Client, clan_tags: list):
    war_logs = {}
    for tag in clan_tags:
        # if we're not allowed to view warlog (private in game),
        # this will raise an exception
        try:
            warlog = await client.get_warlog(tag)
        except coc.PrivateWarLog:
            warlog = []

        war_logs[tag] = warlog

    return war_logs


async def get_clan_tags_names(client: coc.Client, name: str, limit: int):
    clans = await client.search_clans(name=name, limit=limit)
    # return a list of tuples of name/tag pair ie.
    # [(name, tag), (another name, another tag)]
    return [(n.name, n.tag) for n in clans]


async def get_warlog_opponents_from_clan_name(client: coc.Client, name: str, no_of_clans: int):
    clan_tags_names = await get_clan_tags_names(client, name, no_of_clans)

    # search for war logs with clan tags found
    war_logs = await get_warlog_for_clans(client, [n[1] for n in clan_tags_names])

    for name, tag in clan_tags_names:
        # iterate over the wars
        for war in war_logs[tag]:
            # if it is a league war we will error below because it does not
            # return a WarLog object, and thus no opponent
            if war.is_league_entry:
                print("League War Season - No opponent info available")
            else:
                print(f"War: {war.clan.name} vs {war.opponent.name}")


async def main():
    try:
        coc_client = await coc.login(os.environ.get("DEV_SITE_EMAIL"),
                                     os.environ.get("DEV_SITE_PASSWORD"))
    except coc.InvalidCredentials as error:
        exit(error)

    await get_warlog_opponents_from_clan_name(coc_client, "Reddit Zulu", 5)
    await coc_client.close()


if __name__ == "__main__":
    asyncio.run(main())

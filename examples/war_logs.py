import asyncio
import os

import coc
from coc.raid import RaidLogEntry


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


async def test_raidlog(client: coc.Client, clan_tag: str):
    # Limit is set to None retrieving all values
    raid_no_page = await client.get_raidlog(clan_tag)
    limit = len(raid_no_page)
    page_limit = 30

    # Enable pagination, by default it will only cache 10 logs using limit
    # once you iterate beyond the cached amount, it will fetch the next set
    raid_with_page = await client.get_raidlog(clan_tag, page=True, limit=page_limit)

    # Iterate over warlogs like the current version of coc.py
    for i, e in enumerate(raid_no_page):
        e: RaidLogEntry
        print(f"[{i}]-sync limit: {limit} page: False {e.start_time.time}")

    # Option to async for loop a non paginated object
    count = 0
    async for i in raid_no_page:
        print(f"[{count}]-async limit: {limit} page: False")
        count += 1

    for i, e in enumerate(raid_with_page):
        print(f"[{i}]-sync limit: {page_limit} page: True")

    # Set `paginate=True` to enable fetching beyond the limit value until
    # there are more values to fetch
    count = 0
    async for i in raid_with_page:
        print(f"[{count}]-async limit: {page_limit} page: True {i.start_time.time}")
        count += 1


    # Simple test comparing the two data sets
    count = 0
    async for async_log in raid_with_page:
        if async_log != raid_no_page[count]:
            raise AssertionError(f"{id(async_log)} does not match {id(raid_no_page[count])} at index {count}")
        count += 1

async def test_warlog(client: coc.Client, clan_tag: str):

    # Limit is set to None retrieving all values
    warlogs_no_page = await client.get_warlog(clan_tag)
    limit = len(warlogs_no_page)
    pagination_limit = 11

    # Enable pagination, by default it will only cache 10 logs using limit
    # once you iterate beyond the cached amount, it will fetch the next set
    warlogs_with_page = await client.get_warlog(clan_tag, page=True, limit=pagination_limit)

    # Iterate over warlogs like the current version of coc.py
    for i, e in enumerate(warlogs_no_page):
        print(f"[{i}]-sync limit: {limit} page: False")

    # Option to async for loop a non paginated object
    count = 0
    async for i in warlogs_no_page:
        print(f"[{count}]-async limit: {limit} page: False")
        count += 1

    for i, e in enumerate(warlogs_with_page):
        print(f"[{i}]-sync limit: {pagination_limit} page: True")

    # Set `paginate=True` to enable fetching beyond the limit value until
    # there are more values to fetch
    count = 0
    async for i in warlogs_with_page:
        print(f"[{count}]-async limit: {pagination_limit} page: True {i.end_time.time}")
        count += 1

    # Simple test comparing the two data sets
    count = 0
    async for async_log in warlogs_with_page:
        if async_log != warlogs_no_page[count]:
            raise AssertionError(f"{id(async_log)} does not match {id(warlogs_no_page[count])} at index {count}")
        count += 1
    print(count)



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
        for war_log in war_logs[tag]:
            # if it is a league war we will error below because it does not
            # return a WarLog object, and thus no opponent
            if war_log.is_league_entry:
                print("League War Season - No opponent info available")
            else:
                print(f"War: {war_log.clan.name} vs {war_log.opponent.name}")


async def main():
    async with coc.Client() as coc_client:
        try:
            await coc_client.login(os.environ.get("DEV_SITE_EMAIL"),
                                   os.environ.get("DEV_SITE_PASSWORD"))
        except coc.InvalidCredentials as error:
            exit(error)

        await get_warlog_opponents_from_clan_name(coc_client, "Reddit Zulu", 5)
        await test_warlog(coc_client, "#2Y28CGP8")
        await test_raidlog(coc_client, "#2Y28CGP8")


if __name__ == "__main__":
    asyncio.run(main())

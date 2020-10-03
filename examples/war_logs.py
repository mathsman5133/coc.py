import asyncio
import os

try:
    import coc
except ModuleNotFoundError:
    from .. import coc

# email and password is your login credentials used at https://developer.clashofclans.com
client = coc.login(os.environ["DEV_SITE_EMAIL"], os.environ["DEV_SITE_PASSWORD"], key_names="coc.py tests")


async def get_warlog_for_clans(clan_tags: list):
    war_logs = {}
    for tag in clan_tags:
        # if we're not allowed to view warlog (private in game), this will raise an exception
        try:
            warlog = await client.get_warlog(tag)
        except coc.PrivateWarLog:
            warlog = []

        war_logs[tag] = warlog

    # return a dict of list of war logs: {'tag': [list_of_warlog_objects]}
    return war_logs


async def get_clan_tags_names(name: str, limit: int):
    clans = await client.search_clans(name=name, limit=limit)
    # return a list of tuples of name/tag pair ie. [(name, tag), (another name, another tag)]
    return [(n.name, n.tag) for n in clans]


async def get_warlog_opponents_from_clan_name(name: str, no_of_clans: int):
    clan_tags_names = await get_clan_tags_names(name, no_of_clans)

    # search for war logs with clan tags found
    war_logs = await get_warlog_for_clans([n[1] for n in clan_tags_names])

    for name, tag in clan_tags_names:
        # iterate over the wars
        for war in war_logs[tag]:
            # if it is a league war we will error below because it does not return a WarLog object,
            # and thus no opponent
            if war.is_league_entry:
                print("League War Season - No opponent info available")
            else:
                print("War: {} vs {}".format(war.clan.name, war.opponent.name))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_warlog_opponents_from_clan_name("name", 5))

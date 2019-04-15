import coc
import asyncio
import logging

log = logging.getLogger('coc')
log.setLevel(logging.DEBUG)


class COCClient(coc.Client):
    def __init__(self, token, **kwargs):
        super().__init__(token, **kwargs)

    def on_token_reset(self, new_token):
        """We want to override how the default on_token_reset is run
        """
        log.info('New token {} was created!'.format(new_token))


# because we want to update our token if our IP changes, we need to pass in our email and password
# from https://developer.clashofclans.com
cocclient = COCClient('token', email='email', password='password', update_tokens=True)


async def get_warlog_for_clans(clan_tags: list):
    war_logs = {}
    for tag in clan_tags:
        # if we're not allowed to view warlog (private in game), this will raise an exception
        try:
            warlog = await cocclient.get_warlog(tag, cache=True)
        except coc.Forbidden:
            warlog = []

        war_logs[tag] = warlog

    # return a dict of list of war logs: {'tag': [list_of_warlog_objects]}
    return war_logs


async def get_clan_tags_names(name: str, limit: int):
    clans = await cocclient.search_clans(name=name, limit=limit)
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
            if isinstance(war, coc.LeagueWarLogEntry):
                print('League War Season - No opponent info available')
                continue

            print('War: {} vs {}'.format(name, war.opponent.name))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(get_warlog_opponents_from_clan_name('name', 5))
    loop.run_until_complete(cocclient.close())





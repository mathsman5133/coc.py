import asyncio
import logging
import os

import coc
from coc.ext.triggers import CronSchedule, CronTrigger, IntervalTrigger, on_error, start_triggers


coc_client = coc.Client()
cron = CronSchedule('0 0 * * *')
event_loop = asyncio.get_event_loop()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
_logger = logging.getLogger()
MOCK_DATABASE = {'cg_contribution': {}, 'donations': {}}


@on_error()
async def default_error_handler(function_name, arg, exception):
    print('Default error handler engaged')
    print('Default handler:', function_name, arg, exception)


async def special_error_handler(function_name, arg, exception):
    print('Special error handler engaged')
    print('Special handler:', function_name, arg, exception)


@CronTrigger(cron_schedule='0 0 * * 5', iter_args=['#2PP', '#2PPP'], on_startup=False, loop=event_loop, logger=_logger)
async def cache_cg_contribution_before_raid_weekend(player_tag: str):
    """This trigger showcases the `on_startup=False` option and the use of `iter_args`"""

    player = await coc_client.get_player(player_tag)
    MOCK_DATABASE['cg_contribution'][player.tag] = player.clan_capital_contributions

    print('capital gold contributions', MOCK_DATABASE['cg_contribution'])


@CronTrigger(cron_schedule=cron, iter_args=['#2PP'], loop=event_loop, logger=_logger)
async def daily_donation_downloader(clan_tag: str):
    """This trigger showcases the use of a :class:`CronSchedule` object and `iter_args`"""

    clan = await coc_client.get_clan(clan_tag)
    async for member in clan.get_detailed_members():
        MOCK_DATABASE['donations'][member.tag] = member.donations

    print('donation status', MOCK_DATABASE['donations'])


@IntervalTrigger.hourly(loop=event_loop, logger=_logger, error_handler=special_error_handler)
async def test_special_error_handling():
    """This trigger showcases the convenience class methods and the use of a dedicated error handler"""

    return 1/0


@IntervalTrigger(seconds=10, iter_args=[1, 0], autostart=True, loop=event_loop, logger=_logger)
async def test_default_error_handling(divisor: int):
    """This trigger demonstrates the use of `autostart=True` (this is fine because it has no dependencies
    on other resources) in combination with `iter_args` and the default error handler defined by @on_error.
    It also is the trigger with the lowest repeat timer to showcase the fact that triggers indeed do repeat
    """

    return 2/divisor


async def main():
    try:
        await coc_client.login(os.environ.get('DEV_SITE_EMAIL'), os.environ.get('DEV_SITE_PASSWORD'))
    except coc.InvalidCredentials as error:
        exit(error)


if __name__ == "__main__":
    try:
        # using the loop context, run the main function
        event_loop.run_until_complete(main())
        # then start trigger execution
        event_loop.run_until_complete(start_triggers())
        # set the loop to run forever so that it keeps executing the triggers
        event_loop.run_forever()
    except KeyboardInterrupt:
        pass

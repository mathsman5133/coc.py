import asyncio
import functools
import logging

from abc import ABC
from datetime import datetime, timedelta
from traceback import format_exception
from typing import Any, Callable, Coroutine, Optional, Union

# custom components
from cron import CronSchedule


# async def ... function type
CoroFunction = Callable[[], Coroutine[Any, Any, Any]]


class BaseTrigger(ABC):
    """
    Abstract base class for all repeating trigger decorators

    Attributes
    ----------
    iter_args: Optional[:class:`list`]
        an optional list of arguments. The decorated function will be called once per list element,
        and the element will be passed to the decorated function as the first positional argument
    on_startup: Optional[:class:`bool`]
        whether to trigger a run of the decorated function on startup. Defaults to `True`
    error_handler: Optional[:class:`coc.ext.triggers.CoroFunction`]
        an optional function that will be called on each error incurred during the trigger execution
    logger: Optional[:class:`logging.Logger`]
        an optional logger instance implementing the logging.Logger functionality. Debug and error logs
        about the trigger execution will be logged to this logger
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        an optional event loop that the trigger execution will be appended to. If no loop is provided,
        the trigger will provision one using `asyncio.get_event_loop()`
    kwargs:
        any additional keyword arguments that will be passed to the decorated function every time it is called
    """

    def __init__(self,
                 *,  # disable positional arguments
                 iter_args: Optional[list] = None,
                 on_startup: Optional[bool] = True,
                 error_handler: Optional[CoroFunction] = None,
                 logger: Optional[logging.Logger] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 **kwargs):

        self.iter_args = iter_args
        self.on_startup = on_startup
        self.error_handler = error_handler
        self.logger = logger  # TODO: emit warning if no logger or error handler are defined
        self.loop = loop or asyncio.get_event_loop()
        self.kwargs = kwargs

        self.task = None  # placeholder for the repeat task created in self.__wrapper

    def __call__(self, func: CoroFunction):
        return self.__wrapper(func)

    def __wrapper(self, func: CoroFunction):
        """The main workhorse. Handles the repetition of the decorated function
        as well as all logging and error handling
        """

        # fill any passed kwargs
        fixture = functools.partial(func, **self.kwargs)

        @functools.wraps(fixture)
        async def wrapped() -> None:
            async def inner():
                # maybe wait for next trigger cycle
                if not self.on_startup:
                    next_run = self.next_run
                    if self.logger:
                        self.logger.debug(
                            f'`on_startup` is set to `False`. First run of {self.__class__.__name__} for '
                            f'{func.__name__}: {next_run.isoformat()}'
                        )
                    await self.sleep_until(next_run)

                # repeat indefinitely
                while True:
                    if self.logger:
                        self.logger.debug(f'Running {self.__class__.__name__} for {func.__name__}')

                    # call the decorated function
                    try:
                        if self.iter_args:
                            await asyncio.gather(*map(fixture, self.iter_args))
                        else:
                            await fixture()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(''.join(format_exception(type(e), e, e.__traceback__)))
                        # TODO: call error handler (and define proper args for it)

                    # sleep until next execution time
                    next_run = self.next_run
                    if self.logger and datetime.now().astimezone() <= next_run:
                        self.logger.debug(
                            f'{self.__class__.__name__} finished for {func.__name__}. Next run: {next_run.isoformat()}'
                        )
                    elif self.logger:  # i.e. next_run is in the past
                        self.logger.warning(
                            f'{self.__class__.__name__} missed the scheduled run time for {func.__name__}. Running now'
                        )

                    await self.sleep_until(next_run)

            # create a reference to the repeating task to prevent it from accidentally being garbage collected
            self.task = self.loop.create_task(inner())

        if self.logger:
            self.logger.debug(f'{self.__class__.__name__} set up for {func.__name__}')

        return wrapped

    @staticmethod
    async def sleep_until(wakeup_date: datetime):
        """Sleep until a defined point in time. If that point is in the past, don't sleep at all
        Parameters
        ----------
        wakeup_date: :class:`datetime.datetime`
            a timezone-aware datetime at which the trigger should wake up again
        """

        await asyncio.sleep(max((wakeup_date - datetime.now().astimezone()).total_seconds(), 0))

    @property
    def next_run(self) -> datetime:
        """Calculate the date and time of the next run. Needs to be overwritten in subclasses"""
        raise NotImplementedError('All `BaseTrigger` subclasses need to implement `next_run`')


class IntervalTrigger(BaseTrigger):
    """
    A decorator class to repeat a function every `seconds` seconds after the previous execution finishes

    Attributes
    ----------
    seconds: :class:`int`
        how many seconds to wait between trigger runs
    iter_args: Optional[:class:`list`]
        an optional list of arguments. The decorated function will be called once per list element,
        and the element will be passed to the decorated function as the first positional argument
    on_startup: Optional[:class:`bool`]
        whether to trigger a run of the decorated function on startup. Defaults to `True`
    error_handler: Optional[:class:`coc.ext.triggers.CoroFunction`]
        an optional function that will be called on each error incurred during the trigger execution
    logger: Optional[:class:`logging.Logger`]
        an optional logger instance implementing the logging.Logger functionality. Debug and error logs
        about the trigger execution will be logged to this logger
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        an optional event loop that the trigger execution will be appended to. If no loop is provided,
        the trigger will provision one using `asyncio.get_event_loop()`
    kwargs:
        any additional keyword arguments that will be passed to the decorated function every time it is called
    """

    def __init__(self,
                 *,  # disable positional arguments
                 seconds: int,
                 iter_args: Optional[list] = None,
                 on_startup: bool = True,
                 error_handler: Optional[CoroFunction] = None,
                 logger: Optional[logging.Logger] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 **kwargs):

        super().__init__(iter_args=iter_args, on_startup=on_startup, error_handler=error_handler,
                         logger=logger, loop=loop, **kwargs)

        if not isinstance(seconds, int) or seconds <= 0:
            raise ValueError(f'`seconds` must be a positive integer, got {seconds}')
        self._interval_seconds = seconds

    def __str__(self):
        return f'coc.ext.triggers.IntervalTrigger(seconds={self._interval_seconds})'

    @property
    def next_run(self) -> datetime:
        """Calculate the date and time of the next run based on the current time and the defined interval

        Returns
        -------
        the next run date (timezone-aware): :class:`datetime.datetime`
        """

        return datetime.now().astimezone() + timedelta(seconds=self._interval_seconds)


class CronTrigger(BaseTrigger):
    """
    A decorator class to repeat a function based on a Cron schedule

    Attributes
    ----------
    cron_schedule: Union[:class:`str`, :class:`coc.ext.triggers.CronSchedule`]
        the Cron schedule to follow
    iter_args: Optional[:class:`list`]
        an optional list of arguments. The decorated function will be called once per list element,
        and the element will be passed to the decorated function as the first positional argument
    on_startup: Optional[:class:`bool`]
        whether to trigger a run of the decorated function on startup. Defaults to `True`
    error_handler: Optional[:class:`coc.ext.triggers.CoroFunction`]
        an optional function that will be called on each error incurred during the trigger execution
    logger: Optional[:class:`logging.Logger`]
        an optional logger instance implementing the logging.Logger functionality. Debug and error logs
        about the trigger execution will be logged to this logger
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        an optional event loop that the trigger execution will be appended to. If no loop is provided,
        the trigger will provision one using `asyncio.get_event_loop()`
    kwargs:
        any additional keyword arguments that will be passed to the decorated function every time it is called
    """

    def __init__(self,
                 *,  # disable positional arguments
                 cron_schedule: Union[CronSchedule, str],
                 iter_args: Optional[list] = None,
                 on_startup: bool = True,
                 error_handler: Optional[CoroFunction] = None,
                 logger: Optional[logging.Logger] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 **kwargs):

        super().__init__(iter_args=iter_args, on_startup=on_startup, error_handler=error_handler,
                         logger=logger, loop=loop, **kwargs)

        if isinstance(cron_schedule, str):
            cron_schedule = CronSchedule(cron_schedule)
        self.cron_schedule = cron_schedule

    def __str__(self):
        return f'coc.ext.triggers.CronTrigger(cron_schedule="{self.cron_schedule.cron_str}")'

    @property
    def next_run(self) -> datetime:
        """Calculate the date and time of the next run based on the current time and the defined Cron schedule

        Returns
        -------
        the next run date (timezone-aware): :class:`datetime.datetime`
        """

        # prevent multiple runs in one minute
        now = datetime.now().astimezone()
        return self.cron_schedule.next_run_after(now.replace(second=0, microsecond=0) + timedelta(minutes=1))


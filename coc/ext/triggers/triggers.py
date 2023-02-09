import asyncio
import functools

from abc import ABC
from datetime import datetime, timedelta
from traceback import format_exception
from typing import Any, Callable, Coroutine, Optional, Union


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
        self.logger = logger
        self.loop = loop or asyncio.get_event_loop()
        self.kwargs = kwargs

        self.current_execution: Union[datetime, None] = None
        self.task = None  # placeholder for the repeat task created in self.__wrapper

    def __call__(self, func: CoroFunction):
        return self.__wrapper(func)

    def __wrapper(self, func: CoroFunction):
        """the main workhorse. Handles the repetition of the decorated function"""

        # fill any passed kwargs
        fixture = functools.partial(func, **self.kwargs)

        @functools.wraps(fixture)
        async def wrapped() -> None:
            async def inner():
                # maybe wait for next trigger cycle
                if not self.on_startup:
                    self.current_execution = datetime.now()
                    await asyncio.sleep(self._get_sleep_time())

                # repeat indefinitely
                while True:
                    self.current_execution = datetime.now()
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
                    sleep_seconds = self._get_sleep_time()
                    if self.logger and sleep_seconds > 0:
                        next_run = datetime.now() + timedelta(seconds=sleep_seconds)
                        self.logger.debug(
                            f'{self.__class__.__name__} finished for {func.__name__}. Next run: {next_run.isoformat()}'
                        )
                    elif self.logger:  # i.e. sleep_seconds == 0
                        self.logger.warning(
                            f'{self.__class__.__name__} missed the scheduled run time for {func.__name__}. Running now'
                        )

                    await asyncio.sleep(sleep_seconds)

            # create a reference to the repeating task to prevent it from accidentally being garbage collected
            self.task = self.loop.create_task(inner())

        if self.logger:
            self.logger.debug(f'{self.__class__.__name__} set up for {func.__name__}')

        return wrapped

    def _get_sleep_time(self) -> float:
        """calculate the time (in seconds) until the next scheduled run. Needs to be overwritten in subclasses"""
        pass


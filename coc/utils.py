"""
MIT License

Copyright (c) 2019-2020 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import inspect
import calendar
import re

from collections import deque, UserDict
from datetime import datetime, timedelta
from functools import wraps
from operator import attrgetter
from typing import Any, Callable, Generic, Iterable, List, Optional, Type, TypeVar, Tuple, Union


TAG_VALIDATOR = re.compile(r"^#?[PYLQGRJCUV0289]+$")
ARMY_LINK_SEPERATOR = re.compile(r"u(?P<units>[\d+x-]+)|s(?P<spells>[\d+x-]+)")

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


def find(predicate: Callable[[T], Any], iterable: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate.

    For example: ::

        leader = coc.utils.find(lambda m: m.trophies > 5000, clan.members)

    would find the first :class:`~coc.ClanMember` who has more than 5000 trophies and return it.
    If no members have more than 5000 trophies, then ``None`` is returned.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    iterable: iterable
        The iterable to search through.

    Returns
    -------
    The first item in the iterable which matches the predicate passed.
    """
    for element in iterable:
        if predicate(element):
            return element
    return None


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:
    r"""A helper that returns the first item in an iterable that matches the attributes passed.

    If no match is found, ``None`` is returned.

    Example
    -------
    .. code-block:: python3

        member = utils.get(clan.members, level=100, name="Mathsman")
        # returns the first member who has the name "Mathsman" and is level 100

        member = utils.get(clan.members, role=coc.Role.leader)
        # returns the clan leader

        label = utils.get(player.labels, name="Competitive")
        # returns the player's label if they have Competitive.

    Parameters
    ----------
    iterable: iterable
        The list of items to match the attributes from
    \*\*attrs
        A series of kwargs that specify which attributes to match.

    Returns
    -------
    The object from the iterable that matches the attributes passed, or ``None`` if not found.
    """
    converted = [(attrgetter(attr), value) for attr, value in attrs.items()]
    for elem in iterable:
        if all(pred(elem) == value for pred, value in converted):
            return elem
    return None


def from_timestamp(timestamp: str) -> datetime:
    """Parses the raw timestamp given by the API into a :class:`datetime.datetime` object."""
    return datetime.strptime(timestamp, "%Y%m%dT%H%M%S.000Z")


def is_valid_tag(tag: str) -> bool:
    """Validates that a string is a valid Clash of Clans tag.

    This uses the assumption that tags can only consist of the characters PYLQGRJCUV0289.

    Example
    -------

    .. code-block:: python3

        from coc import utils

        user_input = input("Please enter a tag")

        if utils.is_valid_tag(user_input) is True:
            print("{} is a valid tag".format(user_input))
        else:
            print("{} is not a valid tag".format(user_input))

    Returns
    -------
    :class:`bool`
        Whether the tag is a valid tag.
    """
    if TAG_VALIDATOR.match(correct_tag(tag)):
        return True
    return False


def correct_tag(tag: str, prefix: str = "#") -> str:
    """Attempts to correct malformed Clash of Clans tags
    to match how they are formatted in game

    Example
    -------

    .. code-block:: python3

            new_tag = utils.correct_tag(" 123aBc O")
            # new_tag is "#123ABC0".


    Parameters
    ----------
    tag: str
        The tag to correct.
    prefix: str
        The prefix to insert at the start of the tag. Defaults to ``#``.

    Returns
    -------
    str
        The corrected tag.
    """
    return tag and prefix + re.sub(r"[^A-Z0-9]+", "", tag.upper()).replace("O", "0")


def corrected_tag() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Helper decorator to fix tags passed into client calls. The tag must be the first parameter."""

    def deco(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self = args[0]

            if not self.correct_tags:
                return func(*args, **kwargs)

            args = list(args)
            args[1] = correct_tag(args[1])
            return func(*tuple(args), **kwargs)

        return wrapper

    return deco


def parse_army_link(link: str) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Parse an army link into (Troop ID, Quantity) pairs for troops and spells.

    .. note::

        For general usage, consider :meth:`Client.parse_army_link` instead, as it will return Troop and Spell objects.

    Parameters
    ----------
    link: str
        The army link to parse, from in-game.

    Returns
    -------
    List[Tuple[int, int]], List[Tuple[int, int]]
        2 lists containing (troop_id, quantity) pairs. See :meth:`Client.parse_army_link` for a detailed example.

    """
    matches = ARMY_LINK_SEPERATOR.finditer(link)

    units, spells = [], []
    for match in matches:
        if match.group("units"):
            units = [
                (int(split[1]), int(split[0]))
                for split in (troop.split('x') for troop in match.group("units").split('-'))
            ]
        elif match.group("spells"):
            spells = [
                (int(split[1]), int(split[0]))
                for split in (spell.split('x') for spell in match.group("spells").split('-'))
            ]

    return units, spells


def maybe_sort(
        seq: Iterable[T], sort: bool, itr: bool = False, key: Callable[[str], Any] = attrgetter("order")
) -> Union[List[T], Iterable[T]]:
    """Returns list or iter based on itr if sort is false otherwise sorted
    with key defaulting to operator.attrgetter('order')
    """
    return (list, iter)[itr](n for n in sorted(seq, key=key)) if sort else (list, iter)[itr](n for n in seq)


def item(
    _object,
    *,
    index: bool = False,
    index_type: Union[int, str] = 0,
    attribute: str = None,
    index_before_attribute: bool = True
):
    """Returns an object, an index, and/or an attribute of the object."""
    attr_get = attrgetter(attribute or "")
    if not (index or index_type or attribute):
        return _object
    if (index or index_type) and not attribute:
        return _object[index_type]
    if attribute and not (index or index_type):
        return attr_get(_object)
    if index_before_attribute:
        return attr_get(_object[index_type])
    return attr_get(_object)[index_type]


def custom_isinstance(obj, module, name):
    """Helper utility to do an `isinstance` check without importing the module (circular imports)"""
    # pylint: disable=broad-except
    for cls in inspect.getmro(type(obj)):
        try:
            if cls.__module__ == module and cls.__name__ == name:
                return True
        except Exception:
            pass
    return False


async def maybe_coroutine(function_, *args, **kwargs):
    """Returns the result of a function which may or may not be a coroutine."""
    value = function_(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value

    return value


def get_season_start(month: Optional[int] = None, year: Optional[int] = None) -> datetime:
    """Get the datetime that the season started.

    This goes by the assumption that SC resets the season on the last monday of every month at 5am UTC.

    .. note::

        If you want the start of the current season, do not pass any parameters in,
        as doing so won't check to ensure the season start is in the past.

    Parameters
    ----------
    month: Optional[int]
        The month to get the season start for. Defaults to the current month/season.
    year: Optional[int]
        The year to get the season start for. Defaults to the current year/season.

    Returns
    -------
    season_start: :class:`datetime.datetime`
        The start of the season.
    """
    # Start date is the last Monday of the month. That's when SC resets the season values
    def get_start_for_month_year(m, y):
        (weekday_of_first_day, days_in_month) = calendar.monthrange(y, m)
        season_start_day = days_in_month - datetime(year=y, month=m, day=days_in_month).weekday()
        return datetime(year=y, month=m, day=season_start_day, hour=5, minute=0, second=0, microsecond=0)

    if month and year:
        # they want a specific month/year combo
        return get_start_for_month_year(month, year)

    now = datetime.utcnow()
    start = get_start_for_month_year(now.month, now.year)
    if now > start:
        # we got the right one, season started this month
        return start

    # season started last month, so let's try it again.
    if now.month == 1:
        month = 12
        year = now.year - 1
    else:
        month = now.month - 1
        year = now.year
    return get_start_for_month_year(month, year)


def get_season_end(month: Optional[int] = None, year: Optional[int] = None) -> datetime:
    """Get the datetime that the season ends.

    This goes by the assumption that SC resets the season on the last monday of every month at 5am UTC.

    .. note::

        If you want the end of the current season, do not pass any parameters in,
        as doing so won't check to ensure the season end is in the future.

    Parameters
    ----------
    month: Optional[int]
        The month to get the season end for. Defaults to the current month/season.
    year: Optional[int]
        The year to get the season end for. Defaults to the current year/season.

    Returns
    -------
    season_end: :class:`datetime.datetime`
        The end of the season.
    """
    if month and year:
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        return get_season_start(next_month, next_year)

    now = datetime.utcnow()
    end = get_season_start(now.month, now.year)
    if end > now:
        return end

    # season ends next month, let's try again
    if now.month == 12:
        month = 1
        year = now.year + 1
    else:
        month = now.month + 1
        year = now.year
    return get_season_start(month, year)


def get_clan_games_start(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the next clan games will start.

    This goes by the assumption that clan games start at 8am UTC at the 22nd of each month.

    .. note::

        If you want the start of the next or running clan games, do not pass any parameters in,
        for any other pass a datetime in the month before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the month before the clan games you want the start of.

    Returns
    -------
    clan_games_start: :class:`datetime.datetime`
        The start of the next or running clan games.
    """
    if time is None:
        time = datetime.utcnow()
    month = time.month
    year = time.year
    this_months_cg_end = datetime(year=time.year, month=time.month, day=28, hour=8, minute=0, second=0)
    if time > this_months_cg_end and month < 12:
        month += 1
    elif time > this_months_cg_end:  # we're at the end of December
        month = 1
        year += 1
    return datetime(year=year, month=month, day=22, hour=8, minute=0, second=0)


def get_clan_games_end(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the next clan games will end.

    This goes by the assumption that clan games end at 8am UTC at the 28th of each month.

    .. note::

        If you want the end of the next or running clan games, do not pass any parameters in,
        for any other pass a datetime in the month before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the month before the clan games you want the end of.

    Returns
    -------
    clan_games_end: :class:`datetime.datetime`
        The end of the next or running clan games.
    """
    if time is None:
        time = datetime.utcnow()
    month = time.month
    year = time.year
    this_months_cg_end = datetime(year=time.year, month=time.month, day=28, hour=8, minute=0, second=0)
    if time > this_months_cg_end and month < 12:
        month += 1
    elif time > this_months_cg_end:  # we're in December
        month = 1
        year += 1
    return datetime(year=year, month=month, day=28, hour=8, minute=0, second=0)


def get_raid_weekend_start(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the raid weekend will start.

    This goes by the assumption that raid weekends start at friday 7am UTC.

    .. note::

        If you want the start of the next or running raid weekend, do not pass any parameters in,
        for any other pass a datetime in the week before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the week before the raid weekend you want the start of.

    Returns
    -------
    raid_weekend_start: :class:`datetime.datetime`
        The start of the raid weekend.
    """
    if time is None:
        time = datetime.utcnow()
    time = get_raid_weekend_end(time)
    time = time - timedelta(days=3)
    return time


def get_raid_weekend_end(time: Optional[datetime] = None) -> datetime:
    """Get the datetime that the raid weekend will end.

    This goes by the assumption that raid weekends end at monday 7am UTC.

    .. note::

        If you want the end of the next or running raid weekend, do not pass any parameters in,
        for any other pass a datetime in the week before.

    Parameters
    ----------
    time: Optional[datetime]
        Some time in the week before the raid weekend you want the end of.

    Returns
    -------
    raid_weekend_end: :class:`datetime.datetime`
        The end of the raid weekend.
    """
    # Shift the time so that we can pretend the raid ends just after midnight
    if time is None:
        time = datetime.utcnow()
    time = time - timedelta(hours=7, microseconds=1)
    time = time + timedelta(weeks=1, days=-time.weekday())  # Go to the next monday
    time = time.replace(hour=7, minute=0, second=0, microsecond=0)
    return time


class _CachedProperty(Generic[T, T_co]):
    def __init__(self, name: str, function: Callable[[T], T_co]) -> None:
        self.name = name
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance: T, owner: Type[T]) -> T_co:
        try:
            return getattr(instance, self.name)
        except AttributeError:
            result = self.function(instance)
            setattr(instance, self.name, result)
            return result


def cached_property(name: str) -> Callable[[Callable[[T], T_co]], _CachedProperty[T, T_co]]:
    def deco(func: Callable[[T], T_co]) -> _CachedProperty[T, T_co]:
        return _CachedProperty(name, func)
    return deco


class FIFO(UserDict):
    """Implements a FIFO (least-recently-used) dict with a settable max size."""

    __slots__ = (
        "__keys",
        "max_size",
    )

    def __init__(self, max_size):
        self.max_size = max_size
        self.__keys = deque()
        super().__init__()

    def __verify_max_size(self):
        while len(self) > self.max_size:
            del self[self.__keys.popleft()]

    def __setitem__(self, key, value):
        self.__keys.append(key)
        super().__setitem__(key, value)
        self.__verify_max_size()

    def __getitem__(self, key):
        self.__verify_max_size()
        return super().__getitem__(key)

    def __contains__(self, key):
        self.__verify_max_size()
        return super().__contains__(key)

    def copy(self):
        self.data = self.data.copy()
        return self


class HTTPStats(dict):
    """Implements a basic key: deque value to aid with HTTP performance stats."""

    __slots__ = ("max_size",)

    def __init__(self, max_size):
        self.max_size = max_size
        super().__init__()

    def __setitem__(self, key, value):
        try:
            super().__getitem__(key).append(value)
        except (KeyError, AttributeError):
            super().__setitem__(key, deque((value,), maxlen=self.max_size))

    def get_average(self, key):
        """Get the average latency / performance counter for an API endpoint"""
        try:
            stats = self[key]
        except KeyError:
            return None

        return sum(stats) / len(stats)

    def get_mixed_average(self):
        """Get the average latency / performance counter for all API endpoints"""
        stats = [*self.values()]
        return sum(stats) / len(stats)

    def get_all_average(self):
        """Get the average latency / performance counter for each API endpoint."""
        return {k: sum(v) / len(v) for k, v in self.items()}


class CaseInsensitiveDict(dict):
    def __getitem__(self, key):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        return super().__getitem__(key)

    def get(self, key, default=None):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        return super().get(key, default)

    def __setitem__(self, key, v):
        if isinstance(key, tuple):
            key = tuple(x.lower() if isinstance(x, str) else x for x in key)
        else:
            key = key.lower()

        super().__setitem__(key, v)


class UnitStatList(list):
    def __repr__(self):
        return "<UnitStatList {}>".format(super().__repr__())

    def __getitem__(self, i):
        if i == 0:
            raise IndexError("The minimum level is 1, but you tried to get statistics for level 0.")

        return super().__getitem__(i-1)


class UnitStat:
    __slots__ = ("all_levels", )

    def __init__(self, data):
        self.all_levels = UnitStatList(data)

    def __get__(self, instance, owner):
        if instance is None:
            return self.all_levels

        return self[instance.level]

    def __getitem__(self, i):
        return self.all_levels[i]


def _get_maybe_first(dict_items, lookup, default=None):
    try:
        items = dict_items[lookup]
    except KeyError:
        return default
    else:
        try:
            return items[0]
        except (IndexError, KeyError):
            return default

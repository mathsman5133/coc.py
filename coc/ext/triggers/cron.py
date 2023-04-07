import warnings

from calendar import monthrange
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, List, Tuple


LIMITS = [[0, 59], [0, 23], [1, 31], [1, 12], [0, 6]]
NAMES = ['minute', 'hour', 'day_of_month', 'month', 'day_of_week']
CronParts = namedtuple('CronParts', NAMES)


class CronParserError(Exception):
    """Base exception for all errors during Cron string parsing"""

    pass


class CronSchedule:
    """
    A class representing a Cron schedule. It supports the full standard Cron dialect,
    i.e. minute, hour, day of month, month, day of week with list, range and increment modifiers.
    Name aliases for weekdays or months (e.g. Mon, Tue, ... and Jan, Feb, ...) are not supported

    Attributes
    ----------
    cron_str: :class:`str`
        the string representation of the Cron schedule

    Examples
    --------
    "0 0 * * *": run every day at midnight
    "15 0/4 1 * *": run at 15 minutes past every fourth hour on the first day of each month
    "0 * 14,28 * *": run every hour on the 14th and 28th day of each month
    "1/2 * * * 1-5": run every second hour starting at 1:00 AM on Monday through Friday
    """

    def __init__(self, cron_str: str):
        try:
            entries = CronParts(*cron_str.split())
        except (TypeError, ValueError) as e:
            raise CronParserError(
                'Invalid Cron string. A Cron string must consist of exactly five entries separated by '
                'whitespaces: minute, hour, day of month, month, day of week. Example: `0 0 * * *`'
            ) from e

        allowed_values = []
        try:
            for name, entry, limits in zip(NAMES, entries, LIMITS):
                allowed_values.append(self.__parse_entry(name, entry, limits))
        except ValueError as e:
            raise CronParserError(
                f'Invalid Cron string. {name.title()} is malformed. A Cron string element must either be the '
                'wildcard `*` or contain one or more (comma-separated) entries. An entry must contain a time '
                'indicator or a time range `start-end`, and it may contain an increment-suffix separated by a '
                'slash `/`. Example: `4,12-18/2`'
            ) from e

        self.cron_str = cron_str
        self._entries = entries
        self.allowed_values = CronParts(*allowed_values)

    def __str__(self) -> str:
        return self.cron_str

    def __eq__(self, other: Any):
        # two Cron schedules can be considered equal if they allow the same values
        # i.e. Cron('0 0 * * *') == Cron('0 0 1-31 * *')
        return self.__class__ == other.__class__ and self.allowed_values == other.allowed_values

    @staticmethod
    def __parse_entry(name: str, entry: str, limits: List[int]) -> List[int]:
        """Parse a single entry of the cron string"""

        allowed_values = []
        for part in entry.split(','):
            # split off increment
            if '/' in part:
                part, increment = part.split('/')
                increment = int(increment)
                if increment <= 0:
                    raise CronParserError('Invalid Cron string. Increments must be > 0')
            else:
                increment = None

            if part == '*':  # wildcard
                start, end = limits[0], limits[1]
            elif '-' in part:  # time range
                start, end = part.split('-')
                start, end = int(start), int(end)
            else:  # single value
                start = int(part)
                end = limits[1] if increment else start

            if start < limits[0] or end > limits[1]:
                raise CronParserError(
                    f'Invalid Cron string. {name.title()} is out of bounds: must be <= {limits[1]}, '
                    f'>= {limits[0]}, got {start if start < limits[0] else end}'
                )

            if increment:
                allowed_values.extend(list(range(start, end + 1, increment)))
            else:
                allowed_values.extend(list(range(start, end + 1)))
        return sorted(allowed_values)

    @staticmethod
    def __next_allowed_val(value: int, allowed_values: List[int]) -> Tuple[int, bool]:
        """Get the next allowed value from a list of choices and indicate if the list has overflown,
        i.e. whether the next value needs to be incremented"""

        for val in allowed_values:
            if val >= value:
                return val, False
        return allowed_values[0], True

    def __determine_day(self, reference_date: datetime, dow: int, dow_overflow: bool, dom: int, dom_overflow: bool):
        """Solve the OR-relation between day of month and day of week, returning whichever is smaller"""

        # translate day of week into its equivalent day of month
        month_days = monthrange(reference_date.year, reference_date.month)[1]
        dow = reference_date.day + (7 + dow - reference_date.isoweekday()) % 7 + \
            (7 if dow_overflow and reference_date.isoweekday() == dow else 0)
        dow_overflow = dow > month_days
        dow = (dow - 1) % month_days + 1

        # figure out which one is smaller
        if self._entries.day_of_week != '*' and self._entries.day_of_month != '*':
            if dow_overflow and not dom_overflow:
                return dom, dom_overflow
            elif dom_overflow and not dow_overflow:
                return dow, dow_overflow
            elif dom <= dow:
                return dom, dom_overflow
            else:
                return dow, dow_overflow
        elif self._entries.day_of_week != '*':
            return dow, dow_overflow
        else:
            return dom, dom_overflow

    def next_run_after(self, after: datetime) -> datetime:
        """Calculate the next run time of the Cron schedule after a given reference datetime
        Parameters
        ----------
        after: :class:`datetime.datetime`
            the reference datetime

        Returns
        -------
        The next run time after the reference datetime for the Cron schedule: :class:`datetime.datetime`.
        If the input datetime was timezone-aware, the return will also be. If the input was timezone-naive,
        so will the return be
        """

        # construct timezone-aware representation of after
        tz_naive = not after.tzinfo
        if tz_naive:
            warnings.warn(
                'The input datetime was datetime-naive. Assuming the time zone of your device for processing. '
                'The return value will be datetime-naive again', category=RuntimeWarning
            )
            after = after.replace(tzinfo=datetime.now().astimezone().tzinfo)

        now_parts = CronParts(after.minute, after.hour, after.day, after.month, after.isoweekday())

        # next run's minute
        next_minute, min_overflow = self.__next_allowed_val(now_parts.minute, self.allowed_values.minute)

        # next run's hour
        next_hour, hr_overflow = self.__next_allowed_val(now_parts.hour + (1 if min_overflow else 0),
                                                         self.allowed_values.hour)
        if hr_overflow or next_hour > now_parts.hour:  # we overflowed into the next hour, backtrack
            next_minute = self.allowed_values.minute[0]

        # next run's day
        next_dow, dow_overflow = self.__next_allowed_val(now_parts.day_of_week + (1 if hr_overflow else 0),
                                                         self.allowed_values.day_of_week)
        next_dom, dom_overflow = self.__next_allowed_val(now_parts.day_of_month + (1 if hr_overflow else 0),
                                                         self.allowed_values.day_of_month)
        if next_dom > monthrange(after.year, after.month)[1]:  # current month doesn't allow this day
            next_dom, dom_overflow = self.allowed_values.day_of_month[0], True
        next_day, day_overflow = self.__determine_day(after, next_dow, dow_overflow, next_dom, dom_overflow)
        if day_overflow or next_day > now_parts.day_of_month:  # backtrack
            next_minute = self.allowed_values.minute[0]
            next_hour = self.allowed_values.hour[0]

        # next run's month & year
        next_month, month_overflow = self.__next_allowed_val(now_parts.month + (1 if day_overflow else 0),
                                                             self.allowed_values.month)
        next_year = after.year + 1 if month_overflow else after.year
        if month_overflow or next_month > now_parts.month:  # backtrack
            next_minute = self.allowed_values.minute[0]
            next_hour = self.allowed_values.hour[0]
            next_dom = self.allowed_values.day_of_month[0]
            next_dow = (monthrange(next_year, next_month)[0] + 1) % 7  # ISO weekday of the next month's first day
            ref = (after.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_day, _ = self.__determine_day(ref, next_dow, dow_overflow, next_dom, dom_overflow)

        if tz_naive:
            return datetime(year=next_year, month=next_month, day=next_day, hour=next_hour, minute=next_minute)
        return datetime(year=next_year, month=next_month, day=next_day, hour=next_hour,
                        minute=next_minute, tzinfo=after.tzinfo)

    @property
    def next_run(self) -> datetime:
        """The next run time for this Cron schedule
        Returns
        -------
        the next run time for this Cron schedule: :class:`datetime.datetime`
        NOTE: the return value will always be timezone-AWARE
        """

        return self.next_run_after(datetime.now().astimezone())

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
import re

from collections import deque
from datetime import datetime
from functools import wraps
from operator import attrgetter
from typing import Union


TAG_VALIDATOR = re.compile("^#?[PYLQGRJCUV0289]+$")


def find(predicate, seq):
    """A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = find(lambda m: m.name == 'Mighty', clan.members)

    would find the first :class:`~coc.BasicPlayer` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    seq: iterable
        The iterable to search through.
    """
    for element in seq:
        if predicate(element):
            return element
    return None


def get(iterable, **attrs):
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`~coc.utils.find`.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.

    Examples
    ---------

    Basic usage:

    .. code-block:: python3

        member = discord.utils.get(clan.members, name='Foo')

    Multiple attribute matching:

    .. code-block:: python3

        channel = discord.utils.get(guild.voice_channels, name='Foo', exp_level=100)

    Parameters
    -----------
    iterable
        An iterable to search through.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        key, value = attrs.popitem()
        pred = attrget(key.replace("__", "."))
        for elem in iterable:
            if pred(elem) == value:
                return elem
        return None

    converted = [(attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


def from_timestamp(timestamp):
    """Parses the raw timestamp given by the API into a :class:`datetime.datetime` object."""
    return datetime.strptime(timestamp, "%Y%m%dT%H%M%S.000Z")


def is_valid_tag(tag):
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


def correct_tag(tag, prefix="#"):
    """Attempts to correct malformed Clash of Clans tags
    to match how they are formatted in game

    Example
    ---------
        ' 123aBc O' -> '#123ABC0'
    """
    return tag and prefix + re.sub(r"[^A-Z0-9]+", "", tag.upper()).replace("O", "0")


def corrected_tag(arg_offset=1, prefix="#", arg_name="tag"):
    """Helper decorator to fix tags passed into client calls."""

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if not args[0].correct_tags:
                return func(*args, **kwargs)

            try:
                args = list(args)
                args[arg_offset] = correct_tag(args[arg_offset], prefix=prefix)
                return func(*tuple(args), **kwargs)
            except KeyError:
                arg = kwargs.get(arg_name)
                if not arg:
                    return func(*args, **kwargs)
                kwargs[arg_name] = correct_tag(arg, prefix)
                return func(*args, **kwargs)

        return wrapper

    return deco


def maybe_sort(seq, sort, itr=False, key=attrgetter("order")):
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


class LRU(dict):
    """Implements a LRU (least-recently-used) dict with a settable max size."""

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

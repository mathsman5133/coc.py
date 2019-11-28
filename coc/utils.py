"""
MIT License

Copyright (c) 2019 mathsman5133

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

from datetime import datetime
from functools import wraps
from operator import attrgetter
from typing import Union


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


def correct_tag(tag, prefix="#"):
    """Attempts to correct malformed Clash of Clans tags
    to match how they are formatted in game

    Example
    ---------
        ' 123aBc O' -> '#123ABC0'
    """
    return prefix + re.sub(r"[^A-Z0-9]+", "", tag.upper()).replace("O", "0")


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

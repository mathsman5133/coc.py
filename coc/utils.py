import inspect
import re

from datetime import datetime
from functools import wraps
from operator import attrgetter
from typing import Union


def find(predicate, seq):
    for element in seq:
        if predicate(element):
            return element
    return None


def get(iterable, **attrs):
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attrs.items()
    ]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


def from_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y%m%dT%H%M%S.000Z')


def correct_tag(tag, prefix='#'):
    """Attempts to correct malformed Clash of Clans tags
    to match how they are formatted in game
    
    Example
    ---------
        ' 123aBc O' -> '#123ABC0'
    """
    return prefix + re.sub(r'[^A-Z0-9]+', '', tag.upper()).replace('O', '0')


def corrected_tag(arg_offset=1, prefix='#', arg_name='tag'):
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


def maybe_sort(seq, sort, itr=False, key=attrgetter('order')):
    """Returns list or iter based on itr if sort is false otherwise sorted
    with key defaulting to operator.attrgetter('order')
    """
    return (list, iter)[itr](n for n in sorted(seq, key=key)) \
        if sort else (list, iter)[itr](n for n in seq)


def item(
        _object, *, index: bool = False, index_type: Union[int, str] = 0,
        attribute: str = None, index_before_attribute: bool = True
):
    """Returns an object, an index, and/or an attribute of the object."""
    attr_get = attrgetter(attribute or '')
    if not (index or index_type or attribute):
        return _object
    if (index or index_type) and not attribute:
        return _object[index_type]
    if attribute and not (index or index_type):
        return attr_get(_object)
    if index_before_attribute:
        return attr_get(_object[index_type])
    return attr_get(_object)[index_type]


async def get_iter(_iterable, index=False, index_type=0, attribute=None, index_before_attribute=True):
    """Retrieves a generator object from an unknown iterable with optional attributes."""
    if inspect.isasyncgen(_iterable):
        return (item(n, index, index_type, attribute, index_before_attribute) async for n in _iterable)
    return (item(n, index, index_type, attribute, index_before_attribute) for n in _iterable)

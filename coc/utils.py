import re
import json

from datetime import datetime


def to_json(model):
    dct = {}
    for attr in dir(model):
        # ignore private methods
        if attr.startswith('_'):
            continue

        value = getattr(model, attr)

        # iterate through lists - may be a list of objects eg. members in war
        if isinstance(value, list):
            for i in value:
                if not isinstance(i, (list, str, bool)):
                    dct[attr] = [to_json(i)] if attr not in dct.keys() else dct[attr].append(to_json(i))
                    continue

                dct[attr] = [to_json(i)] if attr not in dct.keys() else dct[attr].append(to_json(i))

            continue

        # if it is an object attribute
        if not isinstance(value, (list, str, bool)):
            dct[attr] = [to_json(value)] if attr not in dct.keys() else dct[attr].append(to_json(value))
            continue

        # just a bool, string or int now so can safely add to dict
        dct[attr] = [to_json(value)] if attr not in dct.keys() else dct[attr].append(to_json(value))

    return json.loads(dct, separators=(',', ':'), ensure_ascii=True)


def find(predicate, seq):
    for element in seq:
        if predicate(element):
            return element
    return None


def get(iterable, **attrs):
    def predicate(elem):
        for attr, val in attrs.items():
            nested = attr.split('__')
            obj = elem
            for attribute in nested:
                obj = getattr(obj, attribute)

            if obj != val:
                return False
        return True

    return find(predicate, iterable)


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

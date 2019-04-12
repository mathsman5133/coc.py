import json


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




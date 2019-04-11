import json


def to_json(model):
    dct = {}
    for attr, value in model.__dict__.items():
        # ignore private methods
        if attr.startswith('_'):
            continue

        # iterate through lists - may be a list of objects eg. members in war
        if isinstance(value, list):
            for i in value:
                if not isinstance(i, (list, str, bool)):
                    if attr not in dct.keys():
                        dct[attr] = [to_json(i)]
                    else:
                        dct[attr].append(to_json(i))
                    continue
                if attr not in dct.keys():
                    dct[attr] = [to_json(i)]
                else:
                    dct[attr].append(to_json(i))
            continue

        # if it is an object attribute
        if not isinstance(value, (list, str, bool)):
            if attr not in dct.keys():
                dct[attr] = [to_json(value)]
            else:
                dct[attr].append(to_json(value))
            continue

        # just a bool, string or int now so can safely add to dict
        if attr not in dct.keys():
            dct[attr] = [to_json(value)]
        else:
            dct[attr].append(to_json(value))

    return json.dumps(dct, separators=(',', ':'), ensure_ascii=True)




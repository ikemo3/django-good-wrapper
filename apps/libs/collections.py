def duplicated_objects(object_list):
    return [x for x in set(object_list) if object_list.count(x) > 1]


def as_list(x):
    if isinstance(x, list):
        return x
    elif isinstance(x, tuple):
        return list(x)
    else:
        return [x]

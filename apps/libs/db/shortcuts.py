from operator import attrgetter

from django.db.models import Case, IntegerField, Max, Sum, Value, When


def qs_total(qs, key):
    return qs.aggregate(Sum(key))[key + "__sum"] or 0


def qs_max(qs, key):
    return qs.aggregate(Max(key))[key + "__max"] or 0


def qs_total_client_side(qs, key):
    return sum(getattr(record, key) for record in qs)


def qs_last_by(qs, key: str):
    """QuerySetをローカルでkeyでソートして最後のインスタンスを返す"""
    sorted_qs = sorted(qs, key=attrgetter(key))
    return sorted_qs[-1] if sorted_qs else None


def qs_value_list_flat_client_side(qs, key):
    """values_list(key, flat=True)"""
    result = []
    for obj in qs:
        attr_name_list = key.split("__")
        for attr_name in attr_name_list:
            obj = getattr(obj, attr_name)
        result.append(obj)

    return result


def qs_custom_order(qs, key: str, sort_order: tuple):
    cases = []
    for index, value in enumerate(sort_order):
        when_params = {
            key: value,
            "then": Value(index),
        }
        cases.append(When(**when_params))

    return qs.annotate(custom_order=Case(*cases, output_field=IntegerField())).order_by("custom_order")


def qs_split(qs_split_func):
    return qs_split_func(True), qs_split_func(False)

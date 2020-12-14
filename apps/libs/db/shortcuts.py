from django.db.models import Max, Sum


def qs_total(qs, key):
    return qs.aggregate(Sum(key))[key + "__sum"] or 0


def qs_max(qs, key):
    return qs.aggregate(Max(key))[key + "__max"] or 0


def qs_total_client_side(qs, key):
    return sum(getattr(record, key) for record in qs)

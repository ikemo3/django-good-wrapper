from babel import Locale
from django.utils import timezone


def get_short_weekday(weekday: int):
    return Locale("ja", "JP").days["format"]["narrow"][weekday]


def local_now():
    return timezone.localtime(timezone.now())


def local_today():
    return timezone.localtime(timezone.now()).date()

from datetime import datetime, time

import pytz
from babel import Locale
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.timezone import make_aware

JAPAN_STANDARD_TIME = pytz.timezone("Asia/Tokyo")


def get_short_weekday(weekday: int):
    return Locale("ja", "JP").days["format"]["narrow"][weekday]


def local_now():
    return timezone.localtime()


def local_today():
    return timezone.localdate()


def local_tomorrow():
    return timezone.localdate() + relativedelta(days=1)


def local_today_datetime():
    today = local_today()
    return datetime.combine(today, time())


def make_jst(value):
    return make_aware(value, timezone=JAPAN_STANDARD_TIME).astimezone(pytz.UTC)

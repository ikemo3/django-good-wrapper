from datetime import date, datetime

from django import template
from django.db.models import Model
from django.db.models.fields.files import ImageFieldFile
from django.template.defaultfilters import safe
from django.utils.formats import localize
from django.utils.html import urlize
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime

register = template.Library()


def urlize_with_target_blank(s):
    return mark_safe(urlize(s, nofollow=True, autoescape=True).replace("<a ", '<a target="_blank" '))


@register.filter
def natural_text(obj):
    if isinstance(obj, bool):
        return "はい" if obj is True else "いいえ"

    # 文字列の場合は、空文字の場合も「(なし)」と表示させるが、数値などはそのまま表示させるため、別々に処理
    if isinstance(obj, str):
        return urlize_with_target_blank(obj) if obj else "(なし)"

    if isinstance(obj, datetime):
        return localize(localtime(obj))

    if isinstance(obj, date):
        return localize(obj)

    if isinstance(obj, Model) and hasattr(obj, "get_absolute_url"):
        return safe(f"<a href='{obj.get_absolute_url()}'>{obj}</a>")

    if isinstance(obj, ImageFieldFile):
        if obj:
            # 画像埋め込み
            return safe(f"<img src='{obj.url}'>")
        else:
            return "(なし)"

    if obj is None:
        return "(なし)"

    return urlize_with_target_blank(obj)

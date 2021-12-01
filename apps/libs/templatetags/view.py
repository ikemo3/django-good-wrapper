from django import template
from django.conf import settings

register = template.Library()


@register.filter
def table_columns(obj, view):
    return view.columns(obj)


@register.simple_tag(name="settings")
def get_settings(key):
    return getattr(settings, key, None)


@register.filter(name="startswith")
def do_startswith(text: str, prefix: str):
    if isinstance(text, str):
        return text.startswith(prefix)
    else:
        return False

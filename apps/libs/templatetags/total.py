from types import MethodType

from django import template

register = template.Library()


@register.filter
def total(object_list: list, key: str):
    total_ = 0

    for obj in object_list:
        value = getattr(obj, key)
        if isinstance(value, MethodType):
            value = value()

        total_ += value

    return total_

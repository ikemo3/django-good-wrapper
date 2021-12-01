from django import template

register = template.Library()


@register.filter(name="class")
def get_class(obj):
    return obj.__class__

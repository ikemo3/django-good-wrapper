from django import template
from django.db.models import Field, ForeignKey, Model

register = template.Library()


@register.filter
def list_fields(obj: Model):
    fields = obj._meta.fields

    values = []
    for field in fields:  # type: Field
        if field.name.endswith("_ptr"):
            # 親クラスへのポインタの場合は無視
            continue

        if isinstance(field, ForeignKey):
            value = dict(name=field.verbose_name, value=getattr(obj, field.name))
        elif hasattr(obj, f"get_{field.name}_display"):
            # get_FOO_display がある場合の対応
            method = getattr(obj, f"get_{field.name}_display")
            value = dict(name=field.verbose_name, value=method())
        else:
            value = dict(name=field.verbose_name, value=field.value_from_object(obj))

        values.append(value)

    return values

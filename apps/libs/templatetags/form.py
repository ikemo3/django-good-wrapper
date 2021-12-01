from django import template
from django.db.models import FileField
from django.db.models.query_utils import DeferredAttribute
from django.forms import Field, Form, ModelForm

register = template.Library()


@register.filter
def has_multipart(form: Form) -> bool:
    if not isinstance(form, ModelForm):
        return False

    model = form._meta.model
    fields: dict = form.fields

    for name, _field in fields.items():  # type: str, Field
        if hasattr(model, name):
            model_field = getattr(model, name)  # type: DeferredAttribute
            if isinstance(model_field.field, FileField):
                return True

    return False

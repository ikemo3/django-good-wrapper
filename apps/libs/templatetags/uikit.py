import types

from django import template
from django.forms import (
    CheckboxInput,
    DateInput,
    DateTimeInput,
    Field,
    Form,
    NumberInput,
    RadioSelect,
    Select,
    Textarea,
    TextInput,
    URLInput,
    Widget,
)
from django_filters.widgets import RangeWidget

from apps.libs.forms.widgets import create_select_create_option

register = template.Library()


@register.filter
def uikit(form: Form):
    fields: dict = form.fields

    for name, field in fields.items():  # type: str, Field
        widget: Widget = field.widget
        if isinstance(widget, Textarea):
            widget.attrs["class"] = "uk-textarea"
        elif isinstance(widget, URLInput):
            widget.attrs["class"] = "uk-input"
        elif isinstance(widget, DateTimeInput):
            widget.attrs["class"] = "uk-input"
        elif isinstance(widget, DateInput):
            widget.attrs["class"] = "uk-input"
            widget.input_type = "date"
        elif isinstance(widget, TextInput):
            widget.attrs["class"] = "uk-input"
        elif isinstance(widget, NumberInput):
            widget.attrs["class"] = "uk-input"

            # 'min' 属性が存在して0以上なら inputmode=decimal をセット
            attr_min = widget.attrs.get("min")
            if attr_min is not None and attr_min >= 0:
                widget.attrs["inputmode"] = "decimal"
        elif isinstance(widget, RadioSelect):
            widget.template_name = "widgets/radio.html"
        elif isinstance(widget, CheckboxInput):
            widget.attrs["class"] = "uk-checkbox"
        elif isinstance(widget, Select):
            widget.attrs["class"] = "uk-select"
            widget.create_option = types.MethodType(create_select_create_option(widget.create_option), widget)

            # ForeignKeyの場合、インスタンスを追加するためのURLをセット
            if hasattr(form, "_meta"):
                # noinspection PyProtectedMember
                model = form._meta.model
                model_field = getattr(model, name)
                remote_field = model_field.field.remote_field
                if remote_field:
                    remote_model = remote_field.model
                    if hasattr(remote_model, "get_add_url"):
                        widget.template_name = "widgets/select_foreign_key.html"
                        widget.attrs["data_add_url"] = remote_model.get_add_url()
        elif isinstance(widget, RangeWidget):
            widget.template_name = "includes/multi_widget.html"
            widget.attrs["class"] = "uk-input uk-form-width-small"

    return form

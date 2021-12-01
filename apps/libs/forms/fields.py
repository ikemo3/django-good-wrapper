from django.core.exceptions import ImproperlyConfigured
from django.forms import Field, IntegerField, ModelChoiceField

from apps.libs.forms.widgets import NumberInputWithTaxButton, ReadOnlyWidget, SelectWithData


class PositiveIntegerField(IntegerField):
    def __init__(self, max_value=None, min_value=None, **kwargs):
        if min_value is None:
            min_value = 0
        elif min_value < 0:
            raise ImproperlyConfigured("min_valueは0以上でなければなりません。{}".format(min_value))  # pragma: no cover

        super().__init__(max_value=max_value, min_value=min_value, **kwargs)


class PriceField(PositiveIntegerField):
    widget = NumberInputWithTaxButton

    def __init__(self, max_value=None, min_value=None, **kwargs):
        if "label" not in kwargs:
            kwargs["label"] = "価格(税込)"
        super().__init__(max_value=max_value, min_value=min_value, **kwargs)


class ReadOnlyField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, widget=ReadOnlyWidget, required=False)


class WithFuriganaChoiceField(ModelChoiceField):
    def __init__(self, **kwargs):
        super().__init__(widget=SelectWithData(handler=self.attrs_for_instance), **kwargs)

    @staticmethod
    def attrs_for_instance(attrs, instance):
        attrs.update({"data-search": instance.furigana})
        return attrs

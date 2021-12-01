import contextlib

from django.forms import CheckboxSelectMultiple, NumberInput, Select, Widget


def create_select_create_option(original_method):
    def select_create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = original_method(name, value, label, selected, index, subindex, attrs)

        if hasattr(value, "instance"):
            instance = value.instance

            # django.forms.widgets の実装を見る限り、option["attrs"]はNoneでないことを仮定してよい
            attrs = option.get("attrs")
            assert attrs is not None

            if not attrs.get("data-edit-url") and hasattr(instance, "get_edit_url"):
                with contextlib.suppress(NotImplementedError):
                    attrs["data-edit-url"] = instance.get_edit_url()

        return option

    return select_create_option


class ReadOnlyWidget(Widget):
    template_name = "widgets/readonly.html"


class SelectWithData(Select):
    """data-*などの属性にインスタンスごとに値をセットできるSelect"""

    def __init__(self, handler, attrs=None, choices=()):
        self.handler = handler
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        # Django 3.1から、valueは値があるときは ModelChoiceIteratorValue を返すようになっている。
        # https://docs.djangoproject.com/ja/3.1/ref/forms/fields/#iterating-relationship-choices
        if value:
            attrs = self.handler(option["attrs"], value.instance)
            if hasattr(value.instance, "get_edit_url"):
                with contextlib.suppress(NotImplementedError):
                    attrs["data-edit-url"] = value.instance.get_edit_url()

            option["attrs"] = attrs

        return option


class NumberInputWithTaxButton(NumberInput):
    template_name = "widgets/number_with_tax.html"

    def get_context(self, name, value, attrs):
        # Stimulus用設定
        # nameには "purchase-0-price" のように prefix が入っている場合があるので取り除いてからセット
        last_index = name.rfind("-")
        attrs["data-price-target"] = name[last_index + 1 :]
        return super().get_context(name, value, attrs)


class MultipleCheckbox(CheckboxSelectMultiple):
    template_name = "widgets/multiple_checkbox.html"

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["class"] = "uk-list uk-list-bullet"
        return attrs

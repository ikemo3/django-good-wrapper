from django.forms import Field, Select, Widget


class ReadOnlyWidget(Widget):
    template_name = "widgets/readonly.html"


class ReadOnlyField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, widget=ReadOnlyWidget, required=False)


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
            option["attrs"] = self.handler(option["attrs"], value.instance)

        return option

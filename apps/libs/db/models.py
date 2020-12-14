from typing import Type

from django import forms
from django.db import models
from django.db.models import CharField, Field


class NoteField(CharField):
    def __init__(self):
        kwargs = {"max_length": 200, "verbose_name": "備考", "blank": True, "null": False, "default": ""}
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["verbose_name"]
        del kwargs["blank"]
        del kwargs["default"]
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        # 指定がないときのデフォルトはテキストエリア
        if "widget" not in kwargs:
            kwargs["widget"] = forms.Textarea

        return super().formfield(**kwargs)


def get_model_fields(cls: Type[models.Model]):
    result = []
    for f in cls._meta.get_fields():  # type: Field
        if f.auto_created:
            continue

        result.append(f.name)

    return result

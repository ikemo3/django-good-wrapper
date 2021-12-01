from typing import Type

from django import forms
from django.db import models
from django.db.models import CharField, Field, PositiveSmallIntegerField


class NoteField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 200)
        kwargs.setdefault("verbose_name", "備考")
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", False)
        kwargs.setdefault("default", "")

        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        # 指定がないときのデフォルトはテキストエリア
        if "widget" not in kwargs:
            kwargs["widget"] = forms.Textarea

        return super().formfield(**kwargs)


class IntegerChoiceField(PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        self.cls = kwargs.pop("cls")  # type: Type[models.IntegerChoices]
        kwargs["choices"] = self.cls.choices
        kwargs["default"] = self.cls.default()
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["choices"]
        del kwargs["default"]
        kwargs["cls"] = self.cls
        return name, path, args, kwargs


def get_model_fields(cls: Type[models.Model]):
    result = []
    for f in cls._meta.get_fields():  # type: Field
        if f.auto_created:
            continue

        result.append(f.name)

    return result


def get_raw_verbose_name(cls: Type[models.Model], field_name: str):
    return cls._meta.get_field(field_name).verbose_name

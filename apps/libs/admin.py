from math import ceil
from typing import Type

from django.contrib import admin
from django.db import models
from django.db.models import Field
from django.db.models import Field as ModelField
from django.db.models import ManyToManyField, URLField
from django.forms import Field as FormField
from django.forms import Textarea


class MyAdmin(admin.ModelAdmin):
    """maxlengthに合わせて幅を伸び縮みさせるModelAdmin"""

    ordering = ("id",)

    def formfield_for_dbfield(self, db_field: ModelField, request, **kwargs):
        field: FormField = super().formfield_for_dbfield(db_field, request, **kwargs)
        if field and not isinstance(db_field, URLField):
            maxlength_attr = field.widget.attrs.get("maxlength")
            if maxlength_attr:
                maxlength = int(maxlength_attr)
                if maxlength < 200:
                    field.widget.attrs["size"] = max(maxlength, 20)  # 最低でもsize=20
                    field.widget.attrs["style"] = "width: auto"
                else:
                    # 200文字 → 10行となるように調整
                    rows = ceil(maxlength / 20)
                    field.widget = Textarea(attrs=dict(cols=80, rows=rows))

        return field


def get_model_fields_for_admin(cls: Type[models.Model]):
    """管理画面用にモデルからフィールドを取得する"""
    result = []
    for f in cls._meta.get_fields():  # type: Field
        if f.auto_created:
            continue

        # ManyToManyFieldはそのまま表示できないため対象外
        if isinstance(f, ManyToManyField):
            continue

        result.append(f.name)

    return result


def register_admin(cls, list_display=None):
    from django.contrib.admin.sites import site as default_site

    model_fields = get_model_fields_for_admin(cls)

    class CustomAdmin(MyAdmin):
        list_display = model_fields

    default_site.register(cls, admin_class=CustomAdmin)

    return cls

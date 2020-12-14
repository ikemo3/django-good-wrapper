from math import ceil

from django.contrib import admin
from django.db.models import Field as ModelField
from django.db.models import URLField
from django.forms import Field as FormField
from django.forms import Textarea


class MyAdmin(admin.ModelAdmin):
    """ maxlengthに合わせて幅を伸び縮みさせるModelAdmin """

    ordering = ("id",)

    def formfield_for_dbfield(self, db_field: ModelField, request, **kwargs):
        field: FormField = super().formfield_for_dbfield(db_field, request, **kwargs)
        if field:
            if not isinstance(db_field, URLField):
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

import copy
from datetime import date, datetime
from typing import Dict, Type

import time_machine
from bs4.element import Tag
from dateutil import parser
from django.conf import settings
from django.db import models
from django.db.models import Model
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone
from django.utils.timezone import make_aware
from django_webtest import DjangoWebtestResponse
from webtest import Field, Form, Hidden, Submit, Text, Upload

from apps.libs.datetime import JAPAN_STANDARD_TIME
from apps.libs.factory import UploadFile
from apps.libs.url import remove_next_url


class ObjectItem:
    def __init__(self, item):
        self.item = item

    def link(self):
        return remove_next_url(self.item.select_one("a").get("href"))

    def all_links(self):
        links = [link.get("href") for link in self.item.select("a")]

        # UIkitのdropdownのような、'#'のみは除外
        links = list(filter(lambda link: link != "#", links))

        # '?next=xxx' を除外
        links = [remove_next_url(link) for link in links]
        return links

    def anchor_text(self):
        anchor = self.item.select_one("a")
        if anchor:
            return anchor.get_text()
        else:
            # TODO: アンカーじゃないよね
            return self.item.get_text().strip()

    def text(self):
        item = self.item  # type: Tag

        # 画像の場合はそのsrcを返す
        if item.select_one("img"):
            img = item.select_one("img")
            src = img["src"]
            return src.lstrip(settings.MEDIA_URL)

        return self.item.get_text()


class ObjectItemList(list):
    def __init__(self, item_list):
        super().__init__(list(map(lambda item: ObjectItem(item), item_list)))

    def links(self):
        return [item.link() for item in self]

    def anchor_texts(self):
        return [item.anchor_text() for item in self]

    def texts(self):
        return [item.text() for item in self]


def add_dynamic_field(form: Form, name, value):
    field = Text(form, "input", None, 999, value)
    form.fields[name] = field
    form.field_order.append((name, field))


def get_title(res: DjangoWebtestResponse) -> str:
    return res.html.select_one("title").get_text()


def get_heading(res: DjangoWebtestResponse) -> str:
    h2_list = res.html.select(".body h2")
    assert len(h2_list) == 1
    return h2_list[0].get_text()


def get_input_fields(form: Form) -> list:
    def is_ignorable(f: Field):
        # hiddenは無視
        if isinstance(f, Hidden):
            return True

        # submitボタンは無視
        if isinstance(f, Submit):
            return True

        # ファイルのクリアボタンは無視
        if f.name.endswith("-clear"):
            return True

        return False

    result = []
    fields = form.fields
    for key, fields in fields.items():
        # CSRFトークンは無視
        if key == "csrfmiddlewaretoken":
            continue

        # 入力フィールドのみのときだけ追加
        fields = list(filter(lambda f: not is_ignorable(f), fields))
        if fields:
            result.append(key)

    return result


def prepare_inputs(input_dict: Dict) -> Dict:
    # 一旦全体をコピー
    input_dict_copy = copy.deepcopy(input_dict)

    # Factory などの callable がある場合はそれを呼んだ値に置き換え
    for key, value in input_dict_copy.items():
        if isinstance(value, list):
            new_values = []
            for v in value:
                if callable(v):
                    new_values.append(v())
                else:
                    new_values.append(v)
            input_dict_copy[key] = new_values
        elif callable(value):
            input_dict_copy[key] = value()

    return input_dict_copy


def _prepare_input(value):
    # Factory などの callable がある場合はそれを呼んだ値に置き換え
    if callable(value):
        return value()
    else:
        return value


def _set_form_value(form: Form, key: str, value):
    if isinstance(value, list):
        # MultipleSelectの場合
        form[key] = [v.id for v in value]
    elif isinstance(value, models.Model):
        # インスタンスの場合はそのIDをセット
        form[key] = value.id
    elif isinstance(value, UploadFile):
        form[key] = Upload(value.filename, value.contents)
    else:
        form[key] = value


def _set_form_value_force(form: Form, key: str, value: str):
    # インスタンスの場合はそのIDをセット
    if isinstance(value, models.Model):
        form[key].force_value(value.id)
    else:
        form[key].force_value(value)


def _set_form(form: Form, inputs: Dict):
    # フォーム入力
    for key, value in inputs.items():
        _set_form_value(form, key, value)


def _normalize_value(obj1, obj2):
    # ManyToManyFieldの場合は `.all()` を使って取得
    if hasattr(obj1, "all"):
        obj1 = list(obj1.all())

    # ダウンキャスト可能な場合は行ってから比較
    if hasattr(obj1, "downcast"):
        obj1 = obj1.downcast()

    if hasattr(obj2, "downcast"):
        obj2 = obj1.downcast()

    if isinstance(obj1, ImageFieldFile) and isinstance(obj2, UploadFile):
        return obj1.read(), obj2.contents

    return obj1, obj2


def _normalize_for_display(obj):
    if isinstance(obj, datetime):
        obj = timezone.localtime(obj)
        return obj.strftime("%Y年%-m月%-d日%-H:%M")
    elif isinstance(obj, date):
        return obj.strftime("%Y年%-m月%-d日")
    elif isinstance(obj, bool):
        return "はい" if obj else "いいえ"
    elif obj == "" or obj is None:
        return "(なし)"
    else:
        return str(obj)


def _normalize_record(inputs, record, exclude_keys):
    record_values = dict()
    input_values = dict()
    for key, value in inputs.items():
        if key not in exclude_keys:
            record_value, input_value = _normalize_value(getattr(record, key), value)

            record_values[key] = record_value
            input_values[key] = input_value

    return record_values, input_values


def _get_last_record(model: Type[Model]):
    """モデルの最後に作られたレコードを返す"""
    # idの降順でソートして最初のレコード
    return model.objects.order_by("-id").first()


def freeze_time(s):
    if isinstance(s, str):
        dt = parser.parse(s)
        if timezone.is_naive(dt):
            dt = make_aware(dt, timezone=JAPAN_STANDARD_TIME)
    else:
        dt = s

    return time_machine.travel(dt, tick=False)

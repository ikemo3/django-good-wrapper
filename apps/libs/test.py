import copy
from typing import Dict, Union

import pytest
from django.db import models
from webtest import Form, Hidden, Submit


class ObjectItem:
    def __init__(self, item):
        self.item = item

    def link(self):
        return self.item.select_one("a").get("href")

    def anchor_text(self):
        return self.item.select_one("a").get_text()

    def __repr__(self):
        return repr(self.item)


class ObjectItemList(list):
    def __init__(self, item_list):
        super().__init__(list(map(lambda item: ObjectItem(item), item_list)))

    def links(self):
        return [item.link() for item in self]

    def anchor_texts(self):
        return [item.anchor_text() for item in self]


def get_input_fields(form: Form) -> list:
    result = []
    fields = form.fields
    for key, fields in fields.items():
        # CSRFトークンは無視
        if key == "csrfmiddlewaretoken":
            continue

        assert len(fields) == 1
        field = fields[0]

        # hiddenは無視
        if isinstance(field, Hidden):
            continue

        # submitボタンは無視
        if isinstance(field, Submit):
            continue

        result.append(key)

    return result


def _prepare_inputs(input_dict: Dict) -> Dict:
    # 一旦全体をコピー
    input_dict_copy = copy.deepcopy(input_dict)

    # Factory などの callable がある場合はそれを呼んだ値に置き換え
    for key, value in input_dict_copy.items():
        if callable(value):
            input_dict_copy[key] = value()

    return input_dict_copy


def _set_form_value(form: Form, key: str, value: str):
    # インスタンスの場合はそのIDをセット
    if isinstance(value, models.Model):
        form[key] = value.id
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
        # インスタンスの場合はそのIDをセット
        _set_form_value(form, key, value)


def _set_form_force(form: Form, inputs: Dict):
    # フォーム入力
    for key, value in inputs.items():
        # インスタンスの場合はそのIDをセット
        _set_form_value_force(form, key, value)


def _eq_with_downcast(obj1, obj2):
    # ダウンキャスト可能な場合は行ってから比較
    if hasattr(obj1, "downcast"):
        obj1 = obj1.downcast()

    if hasattr(obj2, "downcast"):
        obj2 = obj1.downcast()

    return obj1 == obj2


@pytest.mark.django_db(transaction=True)
class GenericTestList:
    url = None
    display_as = None
    object_list_selector = None

    def get_fixture(self):
        raise NotImplementedError("get_fixture(self)を実装してください")

    def get_anchor_text(self, instance):
        raise NotImplementedError("get_anchor_text(self, instance)を実装してください")

    @staticmethod
    def get_edit_urls(instance_list):
        return [instance.get_edit_url() for instance in instance_list]

    def get_anchor_texts(self, instance_list):
        return [self.get_anchor_text(instance) for instance in instance_list]

    def test_list(self, auth0_app):
        instance_list = self.get_fixture()

        # 日付型を正しく処理させるためにDBから読み直し
        for instance in instance_list:
            instance.refresh_from_db()

        res = auth0_app.get(self.url)

        if self.object_list_selector:
            selector = self.object_list_selector
        elif self.display_as == "grouping":
            # TODO: グループ化の検証に対応していない(最初のグループだけ取得)のを修正
            selector = "#object-list-0 > li"
        elif self.display_as == "table":
            selector = "#object-list > tr > td:first-child"
        else:
            selector = "#object-list > li"

        item_list = ObjectItemList(res.html.select(selector))
        assert item_list.links() == self.get_edit_urls(instance_list)
        assert item_list.anchor_texts() == self.get_anchor_texts(instance_list)


@pytest.mark.django_db(transaction=True)
class GenericTestAdd:
    model = None
    url = None
    success_url = None
    form_id = "generic-form"
    minimum_inputs = {}
    maximum_inputs = {}
    # 結果の検証対象外とするキー
    assert_exclude_keys = []
    invalid_values: Dict[str, Union[str, list]] = {}

    def get_url(self):
        return self.url

    def test_display(self, auth0_app):
        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # 入力項目の検証
        form = res.forms[self.form_id]
        assert get_input_fields(form) == list(self.maximum_inputs.keys())

    def test_minimum_inputs(self, auth0_app):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        # フォームに入れる値の準備
        minimum_inputs = _prepare_inputs(self.minimum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, minimum_inputs)

        # 送信正常 & 一覧画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        assert self.model.objects.count() == before_count + 1, "レコード数が1つ増えていること"
        record = self.model.objects.first()

        for key, value in minimum_inputs.items():
            if key not in self.assert_exclude_keys:
                assert _eq_with_downcast(getattr(record, key), value)

    def test_maximum_inputs(self, auth0_app):
        """フォームの値を全部埋めたときのテスト"""
        # フォームに入れる値の準備
        maximum_inputs = _prepare_inputs(self.maximum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 送信正常 & 一覧画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        assert self.model.objects.count() == before_count + 1, "レコード数が1つ増えていること"
        record = self.model.objects.last()

        for key, value in maximum_inputs.items():
            if key not in self.assert_exclude_keys:
                assert _eq_with_downcast(getattr(record, key), value)

    # required_key は conftest.py の pytest_generate_tests で設定される
    def test_required(self, auth0_app, required_key):
        """必須項目が足りてない場合のテスト"""
        # フォームに入れる値の準備
        maximum_inputs = _prepare_inputs(self.maximum_inputs)

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 必須項目を空にする
        form[required_key] = ""

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200

    # invalid_key, invalid_value は conftest.py の pytest_generate_tests で設定される
    def test_invalid_value(self, auth0_app, invalid_key, invalid_value):
        """不正な値のテスト"""
        # フォームに入れる値の準備
        maximum_inputs = _prepare_inputs(self.maximum_inputs)

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 不正な値をセットする
        _set_form_value_force(form, invalid_key, invalid_value)

        # 送信エラー
        res = form.submit()
        assert res.status_code == 200


@pytest.mark.django_db(transaction=True)
class GenericTestEdit:
    model = None
    model_factory = None
    success_url = None
    form_id = "generic-form"
    maximum_inputs = {}

    def get_url(self, instance):
        raise NotImplementedError("get_url(self, instance)を実装してください")

    def test_display(self, auth0_app):
        instance = self.model_factory()

        # 画面取得
        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # 入力項目の検証
        form = res.forms[self.form_id]
        assert get_input_fields(form) == list(self.maximum_inputs.keys())

    # key は conftest.py の pytest_generate_tests で設定される
    def test_edit(self, auth0_app, key):
        instance = self.model_factory()

        # フォームに入れる値の準備
        # TODO: valueがinstanceと異なることを保証するのが望ましい
        maximum_inputs = _prepare_inputs(self.maximum_inputs)
        value = maximum_inputs[key]

        # 画面取得
        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form_value(form, key, value)

        # 送信正常 & 成功画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        instance.refresh_from_db()
        assert _eq_with_downcast(getattr(instance, key), value)


@pytest.mark.django_db(transaction=True)
class GenericTestDelete:
    model = None
    model_factory = None
    success_url = None
    form_id = "generic-delete"

    def get_url(self, instance):
        raise NotImplementedError("get_url(self, instance)を実装してください")

    def test_delete(self, auth0_app):
        instance = self.model_factory()

        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # 削除ボタンを押して削除
        form = res.forms[self.form_id]
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードが削除されたことを確認
        assert self.model.objects.count() == 0

    # TODO: エラーケースの対応


@pytest.mark.django_db(transaction=True)
class GenericTestMonthArchive:
    url = None
    display_as = None

    def get_fixture(self):
        raise NotImplementedError("get_fixture(self)を実装してください")

    def get_anchor_text(self, instance):
        raise NotImplementedError("get_anchor_text(self, instance)を実装してください")

    @staticmethod
    def get_edit_urls(instance_list):
        return [instance.get_edit_url() for instance in instance_list]

    def get_anchor_texts(self, instance_list):
        return [self.get_anchor_text(instance) for instance in instance_list]

    def test_list(self, auth0_app):
        instance_list = self.get_fixture()

        res = auth0_app.get(self.url)

        if self.display_as == "grouping":
            # TODO: グループ化の検証に対応していない(最初のグループだけ取得)のを修正
            item_list = ObjectItemList(res.html.select("#object-list-0 > li"))
        else:
            item_list = ObjectItemList(res.html.select("#object-list > li"))

        assert item_list.links() == self.get_edit_urls(instance_list)
        assert item_list.anchor_texts() == self.get_anchor_texts(instance_list)

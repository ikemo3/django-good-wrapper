from typing import Dict, Type, Union

import pytest
from django.db.models import Model
from more_itertools import flatten
from webtest import Form

from apps.libs.collections import as_list
from apps.libs.str import fqcn
from apps.libs.tests.utils import (
    _get_last_record,
    _normalize_record,
    _prepare_input,
    _set_form,
    _set_form_value_force,
    get_heading,
    get_input_fields,
    get_title,
    prepare_inputs,
)


@pytest.mark.django_db(transaction=True)
class GenericTestInlineFormset:
    parent_model: Type[Model] = None
    child_model: Type[Model] = None
    url = None
    success_url = None
    form_id = "generic-form"
    minimum_inputs = {}
    maximum_inputs = {}
    # 結果の検証対象外とするキー
    assert_exclude_keys = []
    invalid_values: Dict[str, Union[str, list]] = {}

    def get_parent_model(self):
        return self.parent_model

    def get_child_model(self):
        return self.child_model

    def get_form_id(self):
        return self.form_id

    def get_url(self):
        return self.url

    def get_title(self):
        assert self.parent_model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.parent_model._meta.verbose_name + "を追加"

    @staticmethod
    def _get_all_keys(inputs):
        parent_keys = list(inputs["parent"].keys())
        children = inputs["children"]
        children_keys = list(flatten([child.keys() for child in children]))
        return parent_keys + children_keys

    @classmethod
    def parametrize_test_display(cls):
        maximum_inputs = as_list(cls.maximum_inputs)
        keys = GenericTestInlineFormset._get_all_keys(maximum_inputs[0])

        return [("keys", [keys])]

    def test_display(self, auth0_app, keys):
        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        # 入力項目の検証
        form = res.forms[self.form_id]
        assert get_input_fields(form) == list(keys), "入力フィールドの順番が正しくありません。"

    @classmethod
    def parametrize_test_minimum_inputs(cls):
        minimum_inputs = as_list(cls.minimum_inputs)

        return [("minimum_inputs", minimum_inputs)]

    def test_minimum_inputs(self, auth0_app, minimum_inputs):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        self.assert_minimum_inputs(
            auth0_app, self.get_url(), self.success_url, minimum_inputs, self.assert_exclude_keys
        )

    def assert_minimum_inputs(self, auth0_app, url, success_url, minimum_inputs, assert_exclude_keys):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        # フォームに入れる値の準備
        parent_minimum_inputs = minimum_inputs["parent"]

        # 子レコードのための入力値
        children_minimum_inputs_list = [prepare_inputs(i) for i in minimum_inputs["children"]]

        # リストをdictにする
        children_minimum_inputs = {}
        for child in children_minimum_inputs_list:
            children_minimum_inputs.update(child)

        # 検証に使用するため、レコード数を保存
        before_count_parent = self.get_parent_model().objects.count()
        before_count_children = self.get_child_model().objects.count()

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, dict(parent_minimum_inputs, **children_minimum_inputs))

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == success_url

        # レコードの中身確認
        assert self.get_parent_model().objects.count() == before_count_parent + 1, "レコード数が1つ増えていること"
        assert self.get_child_model().objects.count() == before_count_children + len(children_minimum_inputs)
        parent_record = _get_last_record(self.get_parent_model())

        # 親レコードの中身確認
        record_values, input_values = _normalize_record(parent_minimum_inputs, parent_record, assert_exclude_keys)
        assert record_values == input_values

        # 子レコードの中身確認
        child_records = list(self.get_child_model().objects.order_by("id"))
        for i, child_record in enumerate(child_records):
            # 子レコードの入力値を取得
            child_inputs = children_minimum_inputs_list[i]
            for child_key in child_inputs.keys():
                value = child_inputs[child_key]
                # rankings-0-strength → strength のように取得
                record_key = child_key.split("-")[2]

                record_values, input_values = _normalize_record({record_key: value}, child_record, assert_exclude_keys)
                assert record_values == input_values

        self.after_test_minimum_inputs(parent_record)

    def after_test_minimum_inputs(self, record):
        pass

    @classmethod
    def parametrize_test_maximum_inputs(cls):
        maximum_inputs = as_list(cls.maximum_inputs)

        return [("maximum_inputs", maximum_inputs)]

    def test_maximum_inputs(self, auth0_app, maximum_inputs):
        """フォームの値を全部埋めたときのテスト"""
        self.assert_maximum_inputs(
            auth0_app, self.get_url(), self.success_url, maximum_inputs, self.assert_exclude_keys
        )

    def assert_maximum_inputs(self, auth0_app, url, success_url, maximum_inputs, assert_exclude_keys):
        """フォームの値を全部埋めたときのテスト"""
        # フォームに入れる値の準備
        parent_maximum_inputs = maximum_inputs["parent"]

        # 子レコードのための入力値
        children_maximum_inputs_list = [prepare_inputs(i) for i in maximum_inputs["children"]]

        # リストをdictにする
        children_maximum_inputs = {}
        for child in children_maximum_inputs_list:
            children_maximum_inputs.update(child)

        # 検証に使用するため、レコード数を保存
        before_count_parent = self.get_parent_model().objects.count()
        before_count_children = self.get_child_model().objects.count()

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, dict(parent_maximum_inputs, **children_maximum_inputs))

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == success_url

        # レコードの中身確認
        assert self.get_parent_model().objects.count() == before_count_parent + 1, "レコード数が1つ増えていること"
        assert self.get_child_model().objects.count() == before_count_children + len(children_maximum_inputs)
        parent_record = _get_last_record(self.get_parent_model())

        # 親レコードの中身確認
        input_values, record_values = _normalize_record(parent_maximum_inputs, parent_record, assert_exclude_keys)
        assert record_values == input_values

        # 子レコードの中身確認
        child_records = list(self.get_child_model().objects.order_by("id"))
        for i, child_record in enumerate(child_records):
            # 子レコードの入力値を取得
            child_inputs = children_maximum_inputs_list[i]
            for child_key in child_inputs.keys():
                value = child_inputs[child_key]
                # rankings-0-strength → strength のように取得
                record_key = child_key.split("-")[2]

                record_values, input_values = _normalize_record({record_key: value}, child_record, assert_exclude_keys)
                assert record_values == input_values

    @classmethod
    def parametrize_test_required(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        maximum_inputs = as_list(cls.maximum_inputs)

        return [
            ("required_key", GenericTestInlineFormset._get_all_keys(minimum_inputs[0])),
            ("maximum_inputs", [maximum_inputs[0]]),
        ]

    def test_required(self, auth0_app, required_key, maximum_inputs):
        """必須項目が足りてない場合のテスト"""
        self.assert_required(auth0_app, self.get_url(), maximum_inputs, required_key)

    def assert_required(self, auth0_app, url, maximum_inputs, required_key):
        """必須項目が足りてない場合のテスト"""
        # フォームに入れる値の準備
        parent_maximum_inputs = maximum_inputs["parent"]

        children_maximum_inputs = {}
        for child in maximum_inputs["children"]:
            children_maximum_inputs.update(prepare_inputs(child))

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.get_form_id()]
        _set_form(form, dict(parent_maximum_inputs, **children_maximum_inputs))

        # 必須項目を空にする(choicesがある場合セットできないため、force_valueを使う)
        form[required_key].force_value("")

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200

    @classmethod
    def parametrize_test_invalid_value(cls):
        invalid_values = cls.invalid_values
        maximum_inputs = as_list(cls.maximum_inputs)
        invalid_values_list = []
        for key, values in invalid_values.items():
            for value in values:
                invalid_values_list.append((key, value))

        return [
            ("invalid_key, invalid_value", invalid_values_list),
            ("maximum_inputs", maximum_inputs),
        ]

    def test_invalid_value(self, auth0_app, invalid_key, invalid_value, maximum_inputs):
        """不正な値のテスト"""
        # フォームに入れる値の準備
        parent_maximum_inputs = maximum_inputs["parent"]

        children_maximum_inputs = {}
        for child in maximum_inputs["children"]:
            children_maximum_inputs.update(prepare_inputs(child))

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, dict(parent_maximum_inputs, **children_maximum_inputs))

        # 不正な値を強制的にセットする
        _set_form_value_force(form, invalid_key, _prepare_input(invalid_value))

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200

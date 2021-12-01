from typing import Dict, Type, Union

import pytest
from django.db.models import Model
from webtest import Form

from apps.libs.collections import as_list
from apps.libs.str import fqcn
from apps.libs.tests.base import NullEntity
from apps.libs.tests.mixins import CreateInstanceTestMixin
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
class GenericTestCopy(CreateInstanceTestMixin):
    src_model_factory = None
    model: Type[Model] = None
    copy_fields = ()
    form_id = "generic-form"
    minimum_inputs = {}
    maximum_inputs = {}
    success_url = None
    # 結果の検証対象外とするキー
    assert_exclude_keys = []
    invalid_values: Dict[str, Union[str, list]] = {}

    @pytest.fixture(autouse=True)
    def pre_check(self):
        assert self.src_model_factory, f"{fqcn(self)}に `src_model_factory` が定義されていません。"
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        assert self.success_url, f"{fqcn(self)}に `success_url` が定義されていません。"

    def get_model(self):
        return self.model

    def get_form_id(self):
        return self.form_id

    def get_url(self, src_instance):
        raise NotImplementedError("get_url(self, src_instance)を実装してください")  # pragma: no cover

    def get_title(self):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "を追加"

    @classmethod
    def parametrize_test_display(cls):
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("maximum_inputs", [maximum_inputs[0]]),
            ("src_model_factory", model_factories),
        ]

    def test_display(self, auth0_app, maximum_inputs, src_model_factory):
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        # 入力項目の検証(順不同)
        form = res.forms[self.form_id]
        expected_input_fields = set(list(maximum_inputs.keys()) + list(self.copy_fields))  # 重複を排除
        assert sorted(get_input_fields(form)) == sorted(expected_input_fields)

        # TODO: 初期値の検証

    @classmethod
    def parametrize_test_minimum_inputs(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("minimum_inputs", minimum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_minimum_inputs(self, auth0_app, minimum_inputs, src_model_factory):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        self.assert_minimum_inputs(
            auth0_app, self.get_url(src_instance), self.success_url, minimum_inputs, self.assert_exclude_keys
        )

    @classmethod
    def parametrize_test_maximum_inputs(cls):
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_maximum_inputs(self, auth0_app, maximum_inputs, src_model_factory):
        """フォームの値を全部埋めたときのテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        self.assert_maximum_inputs(
            auth0_app, self.get_url(src_instance), self.success_url, maximum_inputs, self.assert_exclude_keys
        )

    @classmethod
    def parametrize_test_required(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("required_key", minimum_inputs[0].keys()),
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_required(self, auth0_app, required_key, maximum_inputs, src_model_factory):
        """必須項目が足りてない場合のテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        self.assert_required(auth0_app, self.get_url(src_instance), maximum_inputs, required_key)

    @classmethod
    def parametrize_test_invalid_value(cls):
        invalid_values = cls.invalid_values
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)
        invalid_values_list = []
        for key, values in invalid_values.items():
            for value in values:
                invalid_values_list.append((key, value))

        return [
            ("invalid_key, invalid_value", invalid_values_list),
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_invalid_value(self, auth0_app, invalid_key, invalid_value, maximum_inputs, src_model_factory):
        """不正な値のテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()

        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 不正な値をセットする
        _set_form_value_force(form, invalid_key, _prepare_input(invalid_value))

        # 送信エラー
        res = form.submit()
        assert res.status_code == 200

    def test_not_found(self, auth0_app):
        # 画面取得
        res = auth0_app.get(self.get_url(NullEntity()), expect_errors=True)
        assert res.status_code == 404


@pytest.mark.django_db(transaction=True)
class GenericTestMove:
    src_model_factory = None
    model: Type[Model] = None
    copy_fields = ()
    form_id = "generic-form"
    minimum_inputs = {}
    maximum_inputs = {}
    success_url = None
    # 結果の検証対象外とするキー
    assert_exclude_keys = []
    invalid_values: Dict[str, Union[str, list]] = {}

    @pytest.fixture(autouse=True)
    def pre_check(self):
        assert self.src_model_factory, f"{fqcn(self)}に `src_model_factory` が定義されていません。"
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        assert self.success_url, f"{fqcn(self)}に `success_url` が定義されていません。"

    def get_url(self, src_instance):
        raise NotImplementedError("get_url(self, src_instance)を実装してください")  # pragma: no cover

    def get_title(self):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "を追加"

    @classmethod
    def parametrize_test_display(cls):
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("maximum_inputs", [maximum_inputs[0]]),
            ("src_model_factory", model_factories),
        ]

    def test_display(self, auth0_app, maximum_inputs, src_model_factory):
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        # 入力項目の検証(順不同)
        form = res.forms[self.form_id]
        expected_input_fields = set(list(maximum_inputs.keys()) + list(self.copy_fields))  # 重複を排除
        assert sorted(get_input_fields(form)) == sorted(expected_input_fields)

    @classmethod
    def parametrize_test_minimum_inputs(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("minimum_inputs", minimum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_minimum_inputs(self, auth0_app, minimum_inputs, src_model_factory):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        src_model_class = src_instance._meta.model

        # フォームに入れる値の準備
        minimum_inputs = prepare_inputs(minimum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()
        before_src_count = src_model_class.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, minimum_inputs)

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        assert self.model.objects.count() == before_count + 1, "コピー先のレコード数が1つ増えていること"
        assert src_model_class.objects.count() == before_src_count - 1, "コピー元のレコードが1つ減っていること"
        record = _get_last_record(self.model)

        record_values, input_values = _normalize_record(minimum_inputs, record, self.assert_exclude_keys)
        assert record_values == input_values

        self.after_test_minimum_inputs(record)

    def after_test_minimum_inputs(self, record):
        pass

    @classmethod
    def parametrize_test_maximum_inputs(cls):
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_maximum_inputs(self, auth0_app, maximum_inputs, src_model_factory):
        """フォームの値を全部埋めたときのテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        src_model_class = src_instance._meta.model

        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()
        before_src_count = src_model_class.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 送信正常 & 次の画面に移動
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        assert self.model.objects.count() == before_count + 1, "コピー先のレコード数が1つ増えていること"
        assert src_model_class.objects.count() == before_src_count - 1, "コピー元のレコードが1つ減っていること"
        record = _get_last_record(self.model)

        input_values, record_values = _normalize_record(maximum_inputs, record, self.assert_exclude_keys)
        assert record_values == input_values

    @classmethod
    def parametrize_test_required(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)

        return [
            ("required_key", minimum_inputs[0].keys()),
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_required(self, auth0_app, required_key, maximum_inputs, src_model_factory):
        """必須項目が足りてない場合のテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        src_model_class = src_instance._meta.model

        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()
        before_src_count = src_model_class.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # フォーム入力
        form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 必須項目を空にする(choicesがある場合セットできないため、force_valueを使う)
        form[required_key].force_value("")

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200

        # レコードの検証
        assert self.model.objects.count() == before_count, "コピー先のレコード数が変わらないこと"
        assert src_model_class.objects.count() == before_src_count, "コピー元のレコードが変わらないこと"

    @classmethod
    def parametrize_test_invalid_value(cls):
        invalid_values = cls.invalid_values
        maximum_inputs = as_list(cls.maximum_inputs)
        model_factories = as_list(cls.src_model_factory)
        invalid_values_list = []
        for key, values in invalid_values.items():
            for value in values:
                invalid_values_list.append((key, value))

        return [
            ("invalid_key, invalid_value", invalid_values_list),
            ("maximum_inputs", maximum_inputs),
            ("src_model_factory", model_factories),
        ]

    def test_invalid_value(self, auth0_app, invalid_key, invalid_value, maximum_inputs, src_model_factory):
        """不正な値のテスト"""
        # コピー元のインスタンスを作成
        src_instance = src_model_factory()
        src_model_class = src_instance._meta.model

        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 検証に使用するため、レコード数を保存
        before_count = self.model.objects.count()
        before_src_count = src_model_class.objects.count()

        # 画面取得
        res = auth0_app.get(self.get_url(src_instance))
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 不正な値をセットする
        _set_form_value_force(form, invalid_key, _prepare_input(invalid_value))

        # 送信エラー
        res = form.submit()
        assert res.status_code == 200

        # レコードの検証
        assert self.model.objects.count() == before_count, "コピー先のレコード数が変わらないこと"
        assert src_model_class.objects.count() == before_src_count, "コピー元のレコードが変わらないこと"

    def test_not_found(self, auth0_app):
        # 画面取得
        res = auth0_app.get(self.get_url(NullEntity()), expect_errors=True)
        assert res.status_code == 404

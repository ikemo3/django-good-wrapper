from typing import Dict, Type, Union

import pytest
from django.db.models import Model
from webtest import Form

from apps.libs.collections import as_list
from apps.libs.str import fqcn
from apps.libs.tests.base import NullEntity
from apps.libs.tests.mixins import CreateInstanceTestMixin, SingleInstanceTestMixin
from apps.libs.tests.utils import (
    _normalize_value,
    _prepare_input,
    _set_form,
    _set_form_value,
    _set_form_value_force,
    get_heading,
    get_input_fields,
    get_title,
    prepare_inputs,
)


@pytest.mark.django_db(transaction=True)
class GenericTestAdd(CreateInstanceTestMixin):
    model: Type[Model] = None
    url = None
    success_url = None
    form_id = "generic-form"
    minimum_inputs = {}
    maximum_inputs = {}
    # 結果の検証対象外とするキー
    assert_exclude_keys = []
    invalid_values: Dict[str, Union[str, list]] = {}

    def get_model(self):
        return self.model

    def get_form_id(self):
        return self.form_id

    def get_url(self):
        return self.url

    def get_title(self):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "を追加"

    @classmethod
    def parametrize_test_display(cls):
        maximum_inputs = as_list(cls.maximum_inputs)

        return [("maximum_inputs", [maximum_inputs[0]])]

    def test_display(self, auth0_app, maximum_inputs):
        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        # 入力項目の検証
        form = res.forms[self.form_id]
        assert get_input_fields(form) == list(maximum_inputs.keys()), "入力フィールドの順番が正しくありません。"

    @classmethod
    def parametrize_test_minimum_inputs(cls):
        minimum_inputs = as_list(cls.minimum_inputs)

        return [("minimum_inputs", minimum_inputs)]

    def test_minimum_inputs(self, auth0_app, minimum_inputs):
        """フォームの値を必要最小限の値のみ埋めたときのテスト"""
        self.assert_minimum_inputs(
            auth0_app, self.get_url(), self.success_url, minimum_inputs, self.assert_exclude_keys
        )

    @classmethod
    def parametrize_test_maximum_inputs(cls):
        maximum_inputs = as_list(cls.maximum_inputs)

        return [("maximum_inputs", maximum_inputs)]

    def test_maximum_inputs(self, auth0_app, maximum_inputs):
        """フォームの値を全部埋めたときのテスト"""
        self.assert_maximum_inputs(
            auth0_app, self.get_url(), self.success_url, maximum_inputs, self.assert_exclude_keys
        )

    @classmethod
    def parametrize_test_required(cls):
        minimum_inputs = as_list(cls.minimum_inputs)
        maximum_inputs = as_list(cls.maximum_inputs)

        return [
            ("required_key", minimum_inputs[0].keys()),
            ("maximum_inputs", [maximum_inputs[0]]),
        ]

    def test_required(self, auth0_app, required_key, maximum_inputs):
        """必須項目が足りてない場合のテスト"""
        self.assert_required(auth0_app, self.get_url(), maximum_inputs, required_key)

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
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 画面取得
        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 不正な値を強制的にセットする
        _set_form_value_force(form, invalid_key, _prepare_input(invalid_value))

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200


@pytest.mark.django_db(transaction=True)
class GenericTestEdit:
    model: Type[Model] = None
    model_factory = None
    success_url = None
    form_id = "generic-form"
    maximum_inputs = {}
    invalid_values = {}

    def get_url(self, instance):
        raise NotImplementedError("get_url(self, instance)を実装してください")  # pragma: no cover

    def get_title(self):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "を編集"

    @classmethod
    def parametrize_test_display(cls):
        model_factories = as_list(cls.model_factory)
        maximum_inputs_list = as_list(cls.maximum_inputs)

        return (
            ("model_factory", model_factories),
            ("maximum_inputs", [maximum_inputs_list[0]]),
        )

    def test_display(self, auth0_app, model_factory, maximum_inputs):
        instance = model_factory()

        # 画面取得
        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        # 入力項目の検証
        form = res.forms[self.form_id]
        assert get_input_fields(form) == list(maximum_inputs.keys()), "入力フィールドの順番が正しくありません。"

    @classmethod
    def parametrize_test_edit(cls):
        model_factories = as_list(cls.model_factory)
        maximum_inputs_list = as_list(cls.maximum_inputs)

        return (
            ("key", maximum_inputs_list[0].keys()),
            ("model_factory", model_factories),
            ("maximum_inputs", maximum_inputs_list),
        )

    def test_edit(self, auth0_app, key, model_factory, maximum_inputs):
        instance = model_factory()

        # フォームに入れる値の準備
        # TODO: valueがinstanceと異なることを保証するのが望ましい
        maximum_inputs = prepare_inputs(maximum_inputs)
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
        record_value, input_value = _normalize_value(getattr(instance, key), value)
        assert record_value == input_value

    @classmethod
    def parametrize_test_invalid_value(cls):
        model_factories = as_list(cls.model_factory)
        invalid_values = cls.invalid_values
        maximum_inputs = as_list(cls.maximum_inputs)
        invalid_values_list = []
        for key, values in invalid_values.items():
            for value in values:
                invalid_values_list.append((key, value))

        return [
            ("model_factory", model_factories),
            ("invalid_key, invalid_value", invalid_values_list),
            ("maximum_inputs", maximum_inputs),
        ]

    def test_invalid_value(self, auth0_app, model_factory, invalid_key, invalid_value, maximum_inputs):
        """不正な値のテスト"""
        instance = model_factory()

        # フォームに入れる値の準備
        maximum_inputs = prepare_inputs(maximum_inputs)

        # 画面取得
        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # フォーム入力
        form: Form = res.forms[self.form_id]
        _set_form(form, maximum_inputs)

        # 不正な値を強制的にセットする
        _set_form_value_force(form, invalid_key, _prepare_input(invalid_value))

        # 送信するとエラーで戻ってくる
        res = form.submit()
        assert res.status_code == 200

    def test_not_found(self, auth0_app):
        # 画面取得
        res = auth0_app.get(self.get_url(NullEntity()), expect_errors=True)
        assert res.status_code == 404


@pytest.mark.django_db(transaction=True)
class GenericTestDelete(SingleInstanceTestMixin):
    model: Type[Model] = None
    model_factory = None
    success_url = None
    form_id = "generic-delete"
    display_keys = []
    protected_instance_factories = []

    def get_url(self, instance):
        raise NotImplementedError("get_url(self, instance)を実装してください")  # pragma: no cover

    def get_title(self, instance):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "を削除"

    def get_heading(self, instance):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return f"以下の{self.model._meta.verbose_name}を削除しますか?"

    def get_display_keys(self, instance):
        return self.display_keys

    @classmethod
    def parametrize_test_title(cls):
        model_factories = as_list(cls.model_factory)

        return [("model_factory", model_factories)]

    def test_title(self, auth0_app, model_factory):
        assert model_factory, f"{fqcn(self)}に `model_factory` が定義されていません。"
        instance = model_factory()
        instance.refresh_from_db()

        self.assert_title(auth0_app, self.get_url(instance), self.get_title(instance))

    parametrize_test_heading = parametrize_test_title

    def test_heading(self, auth0_app, model_factory):
        assert model_factory, f"{fqcn(self)}に `model_factory` が定義されていません。"
        instance = model_factory()
        instance.refresh_from_db()

        self.assert_heading(auth0_app, self.get_url(instance), self.get_heading(instance))

    parametrize_test_display = parametrize_test_title

    def test_display(self, auth0_app, model_factory):
        assert model_factory, f"{fqcn(self)}に `model_factory` が定義されていません。"
        instance = model_factory()
        instance.refresh_from_db()

        self.assert_display(auth0_app, self.get_url(instance), instance, self.get_display_keys(instance))

    parametrize_test_delete = parametrize_test_title

    def test_delete(self, auth0_app, model_factory):
        instance = model_factory()

        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # 削除ボタンを押して削除
        form = res.forms[self.form_id]
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードが削除されたことを確認
        assert self.model.objects.count() == 0

    def test_not_found(self, auth0_app):
        self.assert_not_found(auth0_app, self.get_url(NullEntity()))

    @classmethod
    def parametrize_test_delete_with_protected(cls):
        return [
            ("model_factory", as_list(cls.model_factory)),
            ("protected_instance_factory, factory_keyword", cls.protected_instance_factories),
        ]

    def test_delete_with_protected(
        self, auth0_app_without_csrf_check, model_factory, protected_instance_factory, factory_keyword
    ):
        instance = model_factory()
        kwargs = {factory_keyword: instance}
        protected_instance_factory(**kwargs)

        res = auth0_app_without_csrf_check.post(self.get_url(instance))
        assert res.status_code == 200

        # 削除されていないことの確認
        instance.refresh_from_db()
        assert instance


@pytest.mark.django_db(transaction=True)
class GenericTestDeleteList:
    model: Type[Model] = None
    model_factory = None
    url = None
    success_url = None
    form_id = "generic-delete-list"

    def get_url(self):
        return self.url

    def get_delete_instances(self):
        raise NotImplementedError("get_delete_instances(self)を実装してください")  # pragma: no cover

    def get_not_delete_instances(self):
        raise NotImplementedError("get_not_delete_instances(self)を実装してください")  # pragma: no cover

    def get_title(self):
        raise NotImplementedError("get_title(self)を実装してください")  # pragma: no cover

    def test_delete(self, auth0_app):
        delete_instances = self.get_delete_instances()
        not_delete_instances = self.get_not_delete_instances()

        res = auth0_app.get(self.get_url())
        assert res.status_code == 200

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == f"以下の{self.get_title()}を削除しますか?"

        # 削除ボタンを押して削除
        form = res.forms[self.form_id]
        res = form.submit()
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードが削除されたことを確認
        assert self.model.objects.count() == len(not_delete_instances)

        for delete_instance in delete_instances:
            assert not self.model.objects.filter(pk=delete_instance.pk).exists()

        for not_delete_instance in not_delete_instances:
            assert self.model.objects.get(pk=not_delete_instance.pk)


@pytest.mark.django_db(transaction=True)
class GenericTestStatusUpdateView:
    statuses = None
    model_factory = None

    def get_url(self, instance, status):
        raise NotImplementedError("get_url(self, instance, status)を実装してください")  # pragma: no cover

    @classmethod
    def parametrize_test_update(cls):
        statuses = list(cls.statuses)

        return [("status", statuses)]

    def test_update(self, auth0_app_without_csrf_check, status):
        instance = self.model_factory()

        # POSTで送信
        res = auth0_app_without_csrf_check.post(self.get_url(instance, status))
        assert res.status_code == 302
        assert res.location == self.success_url

        # レコードの中身確認
        instance.refresh_from_db()
        assert getattr(instance, self.status_key) == status

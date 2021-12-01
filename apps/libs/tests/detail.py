from typing import Type

import pytest
from django.db.models import Model

from apps.libs.collections import as_list
from apps.libs.str import fqcn
from apps.libs.tests.base import NullEntity
from apps.libs.tests.mixins import SingleInstanceTestMixin


@pytest.mark.django_db(transaction=True)
class GenericTestDetail(SingleInstanceTestMixin):
    model: Type[Model] = None
    model_factory = None
    related_model_factories = ()
    display_keys = []
    perspective_keys = []

    def get_url(self, instance):
        raise NotImplementedError("get_url(self, instance)を実装してください")  # pragma: no cover

    def get_title(self, instance):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name

    get_heading = get_title

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

        res = auth0_app.get(self.get_url(instance))
        assert res.status_code == 200

        # パースペクティブの検証
        perspectives = [anchor["data-perspective"] for anchor in list(res.html.select(".perspectives a"))]
        assert perspectives == list(self.perspective_keys)

    @classmethod
    def parametrize_test_perspective(cls):
        model_factories = as_list(cls.model_factory)
        perspective_keys = as_list(cls.perspective_keys)

        return [("model_factory", model_factories), ("perspective_key", perspective_keys)]

    def test_perspective(self, auth0_app, model_factory, perspective_key):
        assert model_factory, f"{fqcn(self)}に `model_factory` が定義されていません。"
        instance = model_factory()
        instance.refresh_from_db()

        # 子インスタンスを作成
        for related_model_factory, key in self.related_model_factories:
            related_model_factory(**{key: instance})

        url = self.get_url(instance) + f"?perspective={perspective_key}"

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200

    def test_not_found(self, auth0_app):
        self.assert_not_found(auth0_app, self.get_url(NullEntity()))

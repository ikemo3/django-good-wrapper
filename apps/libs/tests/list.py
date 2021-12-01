from typing import Type
from unittest import mock

import pytest
from django.db.models import Model
from django.db.models.fields.related import ForwardManyToOneDescriptor

from apps.libs.collections import as_list
from apps.libs.str import fqcn
from apps.libs.tests.base import NullEntity
from apps.libs.tests.utils import ObjectItemList, get_heading, get_title


@pytest.mark.django_db(transaction=True)
class GenericTestList:
    model: Type[Model] = None
    url = None
    perspective_keys = ()
    display_as = None

    def get_fixture(self):
        raise NotImplementedError("get_fixture(self)を実装してください")  # pragma: no cover

    def get_anchor_text(self, instance):
        raise NotImplementedError("get_anchor_text(self, instance)を実装してください")  # pragma: no cover

    def get_anchor_link(self, instance):
        return instance.get_absolute_url()

    def get_action_links(self, instance):
        if hasattr(instance, "get_copy_url"):
            return [instance.get_edit_url(), instance.get_copy_url()]

        return [instance.get_edit_url()]

    def get_title(self):
        assert self.model, f"{fqcn(self)}に `model` が定義されていません。"
        return self.model._meta.verbose_name + "一覧"

    def get_anchor_texts(self, instance_list):
        return [self.get_anchor_text(instance) for instance in instance_list]

    def test_list(self, auth0_app):
        instance_list = self.get_fixture()

        # 日付型を正しく処理させるためにDBから読み直し
        for instance in instance_list:
            instance.refresh_from_db()

        with mock.patch.object(ForwardManyToOneDescriptor, "get_object", side_effect=Exception):
            res = auth0_app.get(self.url)

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        if self.display_as == "table":
            selector = "#object-list > tr > td:first-child"
        else:
            selector = "#object-list > li"
        item_list = ObjectItemList(res.html.select(selector))

        # TODO: POSTで送信するボタンが検知できていない
        for item, instance in zip(item_list, instance_list):
            assert item.all_links() == [self.get_anchor_link(instance)] + list(self.get_action_links(instance))

        assert item_list.anchor_texts() == self.get_anchor_texts(instance_list)

        # パースペクティブの検証
        perspectives = [anchor["data-perspective"] for anchor in list(res.html.select(".perspectives a"))]
        assert perspectives == list(self.perspective_keys)

    @classmethod
    def parametrize_test_perspective(cls):
        perspective_keys = as_list(cls.perspective_keys)

        return [("perspective_key", perspective_keys)]

    def test_perspective(self, auth0_app, perspective_key):
        self.get_fixture()

        # TODO: 子インスタンスを作成
        url = self.url + f"?perspective={perspective_key}"

        # 画面取得
        res = auth0_app.get(url)
        assert res.status_code == 200


@pytest.mark.django_db(transaction=True)
class GenericTestChildList:
    model: Type[Model] = None
    url = None
    parent_model_factory = None
    perspective_keys = ()

    def get_url(self, parent_instance):
        raise NotImplementedError("get_url(self, parent_instance)を実装してください")  # pragma: no cover

    def get_fixture(self, parent_instance):
        raise NotImplementedError("get_fixture(self, parent_instance)を実装してください")  # pragma: no cover

    def get_anchor_text(self, instance):
        raise NotImplementedError("get_anchor_text(self, instance)を実装してください")  # pragma: no cover

    def get_title(self, parent_instance):
        raise NotImplementedError("get_title(self, parent_instance)を実装してください")  # pragma: no cover

    def get_anchor_link(self, instance):
        raise NotImplementedError("get_anchor_link(self, instance)を実装してください")  # pragma: no cover

    def get_action_links(self, instance):
        raise NotImplementedError("get_action_links(self, instance)を実装してください")  # pragma: no cover

    def get_anchor_texts(self, instance_list):
        return [self.get_anchor_text(instance) for instance in instance_list]

    @classmethod
    def parametrize_test_list(cls):
        model_factories = as_list(cls.parent_model_factory)

        return [("parent_model_factory", model_factories)]

    def test_list(self, auth0_app, parent_model_factory):
        parent_instance = parent_model_factory()
        instance_list = self.get_fixture(parent_instance)

        # 日付型を正しく処理させるためにDBから読み直し
        for instance in instance_list:
            instance.refresh_from_db()

        with mock.patch.object(ForwardManyToOneDescriptor, "get_object", side_effect=Exception):
            res = auth0_app.get(self.get_url(parent_instance))

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title(parent_instance)
        assert get_heading(res) == self.get_title(parent_instance)

        selector = "#object-list > li"
        item_list = ObjectItemList(res.html.select(selector))

        # TODO: POSTで送信するボタンが検知できていない
        for item, instance in zip(item_list, instance_list):
            anchor_links = list(filter(lambda link: link is not None, [self.get_anchor_link(instance)]))
            assert item.all_links() == anchor_links + list(self.get_action_links(instance))

        assert item_list.anchor_texts() == self.get_anchor_texts(instance_list)

    def test_not_found(self, auth0_app):
        # 画面取得
        res = auth0_app.get(self.get_url(NullEntity()), expect_errors=True)
        assert res.status_code == 404

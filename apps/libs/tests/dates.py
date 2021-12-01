from typing import Type
from unittest import mock

import pytest
from django.db.models import Model
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor

from apps.libs.collections import as_list
from apps.libs.datetime import local_today
from apps.libs.tests.utils import ObjectItemList, get_heading, get_title


@pytest.mark.django_db(transaction=True)
class GenericTestMonthArchive:
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

    def get_anchor_urls(self, instance_list):
        return [self.get_anchor_link(instance) for instance in instance_list]

    def get_anchor_texts(self, instance_list):
        return [self.get_anchor_text(instance) for instance in instance_list]

    def get_title(self):
        raise NotImplementedError("get_title(self)を実装してください")  # pragma: no cover

    def test_list(self, auth0_app):
        instance_list = self.get_fixture()

        with mock.patch.object(ForwardManyToOneDescriptor, "get_object", side_effect=Exception):
            res = auth0_app.get(self.url)

        # タイトルと見出しの検証
        assert get_title(res) == self.get_title()
        assert get_heading(res) == self.get_title()

        item_list = ObjectItemList(res.html.select("#object-list > li"))

        assert item_list.links() == self.get_anchor_urls(instance_list)
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
        with mock.patch.object(ForwardManyToOneDescriptor, "get_object", side_effect=Exception):
            res = auth0_app.get(url)
        assert res.status_code == 200


@pytest.mark.django_db(transaction=True)
class GenericTestLatestMonthRedirect:
    model = None
    model_factory = None
    url = None

    def get_not_found_url(self, today):
        raise NotImplementedError("get_not_found_url(self)を実装してください")  # pragma: no cover

    def get_latest_url(self, instance):
        raise NotImplementedError("get_latest_url(self)を実装してください")  # pragma: no cover

    def test_not_found(self, auth0_app):
        res = auth0_app.get(self.url)

        today = local_today()
        assert res.status_code == 302
        assert res.location == self.get_not_found_url(today)

    def test_redirect(self, auth0_app):
        instance = self.model_factory()
        instance.refresh_from_db()

        res = auth0_app.get(self.url)

        assert res.status_code == 302
        assert res.location == self.get_latest_url(instance)


@pytest.mark.django_db(transaction=True)
class GenericTestLatestYearRedirect:
    model = None
    model_factory = None
    url = None

    def get_not_found_url(self, today):
        raise NotImplementedError("get_not_found_url(self)を実装してください")  # pragma: no cover

    def get_latest_url(self, instance):
        raise NotImplementedError("get_latest_url(self)を実装してください")  # pragma: no cover

    def test_not_found(self, auth0_app):
        res = auth0_app.get(self.url)

        today = local_today()
        assert res.status_code == 302
        assert res.location == self.get_not_found_url(today)

    def test_redirect(self, auth0_app):
        instance = self.model_factory()
        instance.refresh_from_db()

        res = auth0_app.get(self.url)

        assert res.status_code == 302
        assert res.location == self.get_latest_url(instance)

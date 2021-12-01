from typing import Dict, Tuple

import pytest

from apps.libs.tests.utils import ObjectItemList


@pytest.mark.django_db(transaction=True)
class GenericTestFilter:
    url = None
    patterns: Tuple[Dict, Tuple] = None

    def get_fixture(self):
        raise NotImplementedError("get_fixture(self)を実装してください")  # pragma: no cover

    def get_anchor_link(self, instance):
        raise NotImplementedError("get_anchor_link(self, instance)を実装してください")  # pragma: no cover

    @classmethod
    def parametrize_test_list(cls):
        patterns = list(cls.patterns)

        return [("fields, expected_indexes", patterns)]

    def test_list(self, auth0_app, fields, expected_indexes):
        instances = self.get_fixture()

        res = auth0_app.get(self.url)
        assert res.status_code == 200

        form = res.forms["generic-form"]
        for field_name, field_value in fields.items():
            form[field_name] = field_value

        # 検索実行
        res = form.submit()

        # 結果の検証
        selector = "#object-list li"
        item_list = ObjectItemList(res.html.select(selector))
        expected_instances = [instances[expected_index] for expected_index in expected_indexes]
        expected_links = [self.get_anchor_link(instance) for instance in expected_instances]
        assert sorted(item_list.links()) == sorted(expected_links)  # TODO: 順番も含めて検証


@pytest.mark.django_db(transaction=True)
class GenericTestSort:
    pass

from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.libs.tests import GenericTest


class TestScaffold(GenericTest):
    @pytest.mark.parametrize(
        "field, expected_field",
        (
            ("name:str", 'name = CharField(max_length=100, verbose_name="")'),
            ("created_at", 'created_at = DateTimeField(verbose_name="作成日時", auto_now_add=True)'),
            ("updated_at", 'updated_at = DateTimeField(verbose_name="更新日時", auto_now=True)'),
            ("url", 'url = URLField(verbose_name="URL", blank=True)'),
            ("start_date:date", 'start_date = DateField(verbose_name="")'),
            ("start_time:datetime", 'start_time = DateTimeField(verbose_name="")'),
            ("note:text", 'note = TextField(verbose_name="")'),
            ("is_active:bool", 'is_active = BooleanField(verbose_name="")'),
        ),
    )
    def test_it(self, field, expected_field):
        with patch("apps.libs.management.commands.scaffold.Command.exec") as m:
            call_command("scaffold", "apps.foo", "Foo", field)

        m.assert_called_once()
        (
            directory,
            test_directory,
            init_py,
            models_py,
            urls_py,
            views_py,
            forms_py,
            tests_init_py,
            factories_py,
            tests_py,
            test_models_py,
        ) = m.call_args_list[0].args

        assert directory == "apps/foo"
        assert test_directory == "apps/foo/tests"
        assert init_py == ""

        # models.py
        assert "class FooQuerySet(models.QuerySet)" in models_py
        assert "class FooManager(models.Manager)" in models_py
        assert "class Foo(CRUDLMixin, ActionMixin, models.Model)" in models_py
        assert expected_field in models_py

        # urls.py
        assert "list_view=views.FooListView" in urls_py
        assert "detail_view=views.FooDetailView" in urls_py
        assert "add_view=views.FooAddView" in urls_py
        assert "edit_view=views.FooEditView" in urls_py
        assert "delete_view=views.FooDeleteView" in urls_py

        # views.py
        assert "class FooListView(GenericListView)" in views_py
        assert "class FooDetailView(GenericDetailView)" in views_py
        assert "class FooAddView(GenericAddView)" in views_py
        assert "class FooEditView(GenericEditView)" in views_py
        assert "class FooDeleteView(GenericDeleteView)" in views_py

        # forms.py
        assert "class FooAddForm(forms.ModelForm)" in forms_py
        assert "class FooEditForm(forms.ModelForm)" in forms_py

        assert tests_init_py == ""
        assert "class FooFactory(factory.django.DjangoModelFactory)" in factories_py

        # tests.py
        assert "class TestFooListView(GenericTestList)" in tests_py
        assert "class TestFooDetailView(GenericTestDetail)" in tests_py
        assert "class TestFooAddView(GenericTestAdd)" in tests_py
        assert "class TestFooEditView(GenericTestEdit)" in tests_py
        assert "class TestFooDeleteView(GenericTestDelete)" in tests_py

        # test_models.py
        assert "class TestFoo(GenericTestModel)" in test_models_py

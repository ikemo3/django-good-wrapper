import os

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = "アプリケーションの雛形を作成します。"

    def add_arguments(self, parser):
        parser.add_argument("package", help="パッケージ")
        parser.add_argument("model", help="モデルクラス名を指定")
        parser.add_argument("fields", nargs="+", help="フィールド名を指定(例: name:str)")

    def handle(self, *args, **options):
        package: str = options["package"]
        model: str = options["model"]
        fields: list[str] = options["fields"]
        field_codes: list[str] = []

        for field in fields:
            if field == "created_at":
                field_code = 'created_at = DateTimeField(verbose_name="作成日時", auto_now_add=True)'
                field_codes.append(field_code)
            elif field == "updated_at":
                field_code = 'updated_at = DateTimeField(verbose_name="更新日時", auto_now=True)'
                field_codes.append(field_code)
            elif field == "url":
                field_code = 'url = URLField(verbose_name="URL", blank=True)'
                field_codes.append(field_code)
            else:
                field_name, field_type = field.split(":")
                if field_type == "str":
                    field_code = f'{field_name} = CharField(max_length=100, verbose_name="")'
                    field_codes.append(field_code)
                elif field_type == "date":
                    field_code = f'{field_name} = DateField(verbose_name="")'
                    field_codes.append(field_code)
                elif field_type == "datetime":
                    field_code = f'{field_name} = DateTimeField(verbose_name="")'
                    field_codes.append(field_code)
                elif field_type == "text":
                    field_code = f'{field_name} = TextField(verbose_name="")'
                    field_codes.append(field_code)
                elif field_type == "bool":
                    field_code = f'{field_name} = BooleanField(verbose_name="")'
                    field_codes.append(field_code)
                else:
                    raise CommandError("不明なフィールドの型です。:" + field_type)  # pragma: no cover

        const_package = ".".join(package.split(".")[0:2])
        snake_name = package.split(".")[-1]
        app_name = snake_name.replace("_", "-")
        url_prefix = package.removeprefix("apps.").replace(".", ":").replace("_", "-")
        directory = package.replace(".", "/")
        test_directory = directory + "/tests"

        context = dict(
            package=package,
            const_package=const_package,
            app_name=app_name,
            model_name=model,
            url_prefix=url_prefix,
            has_list=True,
            has_detail=True,
            has_add=True,
            has_edit=True,
            has_delete=True,
            field_codes=field_codes,
        )

        init_py = ""
        models_py = render_to_string("scaffold/models.py.html", context)
        urls_py = render_to_string("scaffold/urls.py.html", context)
        views_py = render_to_string("scaffold/views.py.html", context)
        forms_py = render_to_string("scaffold/forms.py.html", context)
        tests_init_py = ""
        factories_py = render_to_string("scaffold/factories.py.html", context)
        tests_py = render_to_string("scaffold/tests.py.html", context)
        tests_model_py = render_to_string("scaffold/test_models.html", context)
        self.exec(
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
            tests_model_py,
        )

    @staticmethod
    def exec(
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
        tests_model_py,
    ):  # pragma: no cover

        os.makedirs(directory, exist_ok=True)
        os.makedirs(test_directory, exist_ok=True)

        with open(directory + "/__init__.py", "w") as f:
            f.write(init_py)

        with open(directory + "/models.py", "w") as f:
            f.write(models_py)

        with open(directory + "/urls.py", "w") as f:
            f.write(urls_py)

        with open(directory + "/views.py", "w") as f:
            f.write(views_py)

        with open(directory + "/forms.py", "w") as f:
            f.write(forms_py)

        with open(test_directory + "/__init__.py", "w") as f:
            f.write(tests_init_py)

        with open(test_directory + "/factories.py", "w") as f:
            f.write(factories_py)

        with open(test_directory + "/tests.py", "w") as f:
            f.write(tests_py)

        with open(test_directory + "/test_models.py", "w") as f:
            f.write(tests_model_py)

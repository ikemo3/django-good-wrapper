from importlib import import_module

from django import template
from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse
from more_itertools import chunked

register = template.Library()


@register.inclusion_tag("global_menu.html")
def global_menu():

    links = []
    for app_name in settings.GLOBAL_MENU_APPS:
        # AppConfigを取得
        module, class_name = app_name.rsplit(".", 1)
        app_config = getattr(import_module(module), class_name)  # type: AppConfig

        config_name = app_config.name  # type: str
        app_name = config_name[5:]
        verbose_name = app_config.verbose_name
        dashboard_url = reverse(f"{app_name}:dashboard")
        link = {"label": verbose_name, "url": dashboard_url}
        links.append(link)

    menus = [
        {
            "label": "管理",
            "links": [
                {
                    "label": "👮‍管理画面",
                    "url": reverse("admin:index"),
                },
            ],
        },
        {
            "label": "アプリ",
            "links": links,
        },
    ]

    # gridのために2つずつにしてから渡す
    chunked_global_menu = chunked(menus, 2)
    return {
        "global_menu": chunked_global_menu,
    }

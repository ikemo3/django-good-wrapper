from dataclasses import dataclass
from typing import Iterable, List, Type, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin

from apps.libs.actions import Action, AddAction, BulkAddAction, DividerAction, LinkAction, SearchAction, SortAction


def make_add_link(model: Type[Model]):
    if hasattr(model, "get_add_url"):
        return AddAction(label=model._meta.verbose_name + "を追加", url=model.get_add_url)

    raise NotImplementedError(f"{model}にget_add_urlを実装してください。")  # pragma: no cover


def make_bulk_add_link(model: Type[Model]):
    if hasattr(model, "get_bulk_add_url"):
        return BulkAddAction(label=model._meta.verbose_name + "を一括追加", url=model.get_bulk_add_url)

    raise NotImplementedError(f"{model}にget_bulk_add_urlを実装してください。")  # pragma: no cover


def make_list_link(model: Type[Model], label=None):
    if hasattr(model, "get_list_url"):
        if label:
            return LinkAction(label=label, url=model.get_list_url)
        else:
            return LinkAction(label=model._meta.verbose_name + "一覧", url=model.get_list_url)

    raise NotImplementedError(f"{model}にget_list_urlを実装してください。")  # pragma: no cover


def make_sort_link(model: Type[Model]):
    if hasattr(model, "get_sort_url"):
        return SortAction(label=model._meta.verbose_name + "をソート", url=model.get_sort_url)

    raise NotImplementedError(f"{model}にget_sort_urlを実装してください。")  # pragma: no cover


def make_filter_link(model: Type[Model]):
    if hasattr(model, "get_filter_url"):
        return SearchAction(label=model._meta.verbose_name + "を検索", url=model.get_filter_url)

    raise NotImplementedError(f"{model}にget_filter_urlを実装してください。")  # pragma: no cover


def make_latest_year_link(model: Type[Model]):
    if hasattr(model, "get_latest_year_url"):
        return LinkAction(label=model._meta.verbose_name + "(今年)", url=model.get_latest_year_url)

    raise NotImplementedError(f"{model}にget_latest_year_urlを実装してください。")  # pragma: no cover


def make_latest_month_link(model: Type[Model]):
    if hasattr(model, "get_latest_month_url"):
        return LinkAction(label=model._meta.verbose_name + "(今月)", url=model.get_latest_month_url)

    raise NotImplementedError(f"{model}にget_latest_month_urlを実装してください。")  # pragma: no cover


class CRUDLMenu:
    def __init__(self, model: Type[Model], top_link, all_menu):
        self.model = model
        self.top_link = top_link
        self.all_menu = all_menu

    def add_navbar_links(self, extra_menu=()):
        if hasattr(self.model, "get_model_top_link"):
            model_top_link = self.model.get_model_top_link()
        else:
            model_top_link = make_list_link(self.model)

        return self.top_link, model_top_link, *extra_menu, self.all_menu - model_top_link

    def filter_navbar_links(self, extra_menu=()):
        action_links = [make_add_link(self.model)]

        model_top_link = make_list_link(self.model)
        action_links.append(model_top_link)

        return self.top_link, *action_links, *extra_menu, self.all_menu - model_top_link

    @staticmethod
    def _extend_list_common_links(model, action_links):
        # get_add_urlがある場合はそのリンクを追加
        if hasattr(model, "get_add_url"):
            action_links.append(make_add_link(model))

        # get_bulk_add_urlがある場合はそのリンクを追加
        if hasattr(model, "get_bulk_add_url"):
            action_links.append(make_bulk_add_link(model))

        # get_sort_urlがある場合はそのリンクを追加
        if hasattr(model, "get_sort_url"):
            action_links.append(make_sort_link(model))

        # get_filter_urlがある場合はそのリンクを追加
        if hasattr(model, "get_filter_url"):
            action_links.append(make_filter_link(model))

    def list_navbar_links(self, extra_menu=()):
        action_links = []

        # リスト共通のリンクを追加
        self._extend_list_common_links(self.model, action_links)

        return self.top_link, *action_links, *extra_menu, self.all_menu - make_list_link(self.model)

    def year_archive_navbar_links(self, extra_menu=()):
        action_links = []

        # リスト共通のリンクを追加
        self._extend_list_common_links(self.model, action_links)

        # get_latest_month_urlがある場合はそのリンクを追加
        if hasattr(self.model, "get_latest_month_url"):
            action_links.append(make_latest_month_link(self.model))

        return self.top_link, *action_links, *extra_menu, self.all_menu

    def month_archive_navbar_links(self, extra_menu=()):
        action_links = []

        # リスト共通のリンクを追加
        self._extend_list_common_links(self.model, action_links)

        # get_latest_year_urlがある場合はそのリンクを追加
        if hasattr(self.model, "get_latest_year_url"):
            action_links.append(make_latest_year_link(self.model))

        return self.top_link, *action_links, *extra_menu, self.all_menu

    bulk_add_navbar_links = add_navbar_links
    detail_navbar_links = add_navbar_links
    edit_navbar_links = add_navbar_links
    delete_navbar_links = add_navbar_links
    sort_navbar_links = add_navbar_links
    select_navbar_links = add_navbar_links
    formset_navbar_links = add_navbar_links


LINK_TO_ADMIN = LinkAction(label="管理画面", url=reverse_lazy("admin:index"))
DIVIDER = DividerAction()


@dataclass
class Menu:
    submenus: List[Action]
    has_submenu: bool = True


class NavbarMixin(ContextMixin):
    """
    ナビゲーションバー用の情報を渡すためのMixin。
    継承時はGeneric Viewより前に指定すること。
    """

    # デフォルトは「トップに戻る」のみ
    navbar_links: Union[Iterable[Action], Action] = LINK_TO_ADMIN
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()

        if self.menu:
            extra_menu = self.get_extra_menu()
            self.navbar_links = self.default_navbar_links(self.menu, extra_menu)
        elif self.get_navbar_links():
            self.navbar_links = self.get_navbar_links()
        else:
            self.navbar_links = LINK_TO_ADMIN

    @staticmethod
    def get_navbar_links():
        return ()

    @staticmethod
    def get_extra_menu():
        return ()

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        raise NotImplementedError("default_navbar_links(menu, extra_menu)を実装してください。")  # pragma: no cover

    @property
    def extra_context(self):
        menus: List[Union[Action, Menu]] = []
        if self.navbar_links is not None:
            if isinstance(self.navbar_links, (list, tuple)):
                for navbar_link in self.navbar_links:
                    if isinstance(navbar_link, (list, tuple)):
                        # サブメニューがある場合
                        menus.append(Menu(has_submenu=True, submenus=navbar_link))
                    else:
                        menus.append(navbar_link)
            elif isinstance(self.navbar_links, Action):
                menus.append(self.navbar_links)
            else:
                raise ImproperlyConfigured(
                    "navbar_linksが正しく定義されていません。ActionまたはActionのリスト/タプルでないといけません。"
                )  # pragma: no cover
        else:
            raise ImproperlyConfigured("navbar_linksが定義されていません。")  # pragma: no cover

        return {"navbar_links": menus}

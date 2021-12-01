from typing import List, Tuple, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from apps.libs.actions import LinkAction
from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.perspective import ListViewPerspectiveMixin, Perspective
from apps.libs.views_mixin import ObjectListNameMixin, ObjectNameMixin


class GenericListView(ListViewPerspectiveMixin, ObjectListNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    template_name = "generic/generic_list.html"

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset and not self.get_queryset:
            raise ImproperlyConfigured("Viewに `model` または `queryset` または `get_queryset()` が未定義です。")  # pragma: no cover

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.list_navbar_links(extra_menu)

    def get_perspectives(self) -> List[Perspective]:
        perspectives = super().get_perspectives()
        if perspectives:
            return perspectives

        return self.get_list_perspectives(self.model)

    @staticmethod
    def summaries():
        return ()


class GenericChildListView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    template_name = "generic/generic_list.html"
    parent_model = None
    child_model = None
    parent_key = None

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset and not self.get_queryset:
            raise ImproperlyConfigured("Viewに `model` または `queryset` または `get_queryset()` が未定義です。")  # pragma: no cover

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.parent_object = get_object_or_404(self.parent_model, id=kwargs["pk"])

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.detail_navbar_links(extra_menu)

    def get_queryset(self) -> QuerySet:
        kwargs = dict()
        kwargs[self.parent_key] = self.parent_object.id
        return self.child_model.objects.filter(**kwargs)

    def get_object_name(self):
        return str(self.parent_object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.parent_object
        context["extra_buttons"] = self.get_extra_buttons()

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()

        return context

    def get_extra_buttons(self) -> Union[List, Tuple]:
        # 子インスタンスを作るボタンをデフォルトで追加
        if hasattr(self.child_model, "get_add_url"):
            obj = self.parent_object
            label = f"{self.child_model._meta.verbose_name}を追加"
            url = self.child_model.get_add_url() + f"?{self.parent_key}={obj.id}"
            item_add_action = LinkAction(label=label, url=url)
            return [item_add_action]
        else:
            return ()

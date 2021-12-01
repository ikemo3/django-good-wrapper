from typing import List, Tuple, Union

from django_filters.views import FilterView

from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.views.multiple import MultipleFilterView


class GenericFilterView(Auth0LoginRequiredMixin, NavbarMixin, FilterView):
    template_name = "generic/generic_filter.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.filter_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extra_buttons"] = self.get_extra_buttons()
        return context

    @staticmethod
    def get_extra_buttons() -> Union[List, Tuple]:
        return ()


class GenericMultipleFilterView(Auth0LoginRequiredMixin, NavbarMixin, MultipleFilterView):
    template_name = "generic/generic_filter_multiple.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        raise NotImplementedError("default_navbar_links(menu, extra_menu)を実装してください。")  # pragma: no cover

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extra_buttons"] = self.get_extra_buttons()
        return context

    @staticmethod
    def get_extra_buttons() -> Union[List, Tuple]:
        return ()

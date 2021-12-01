from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import RedirectView, TemplateView, View

from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.views_mixin import SupportNextUrlMixin


class GenericRedirectView(SupportNextUrlMixin, Auth0LoginRequiredMixin, RedirectView):
    pass


class GenericView(Auth0LoginRequiredMixin, View):
    pass


class GenericTemplateView(Auth0LoginRequiredMixin, NavbarMixin, TemplateView):
    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        raise ImproperlyConfigured("GenericTemplateViewにmenuは定義しないでください。")  # pragma: no cover

from django.core.exceptions import ImproperlyConfigured
from django.views.generic import MonthArchiveView, RedirectView, YearArchiveView

from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.datetime import local_today
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.perspective import ListViewPerspectiveMixin
from apps.libs.views_mixin import ObjectNameMixin


class GenericMonthArchiveView(
    ListViewPerspectiveMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, MonthArchiveView
):
    month_format = "%m"
    allow_empty = True
    date_field = "date"
    template_name = "generic/generic_archive_month.html"

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset:
            raise ImproperlyConfigured("Viewに `model` または `queryset` が未定義です。")  # pragma: no cover

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.month_archive_navbar_links(extra_menu)

    def get_month_url(self, year, month):
        raise NotImplementedError("get_month_url(year, month) を再定義してください。")  # pragma: no cover

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 今月へのリンク
        this_month = context["month"]
        context["this_month_url"] = self.get_month_url(this_month.year, this_month.month)

        # 前月へのリンク(常にある)
        previous_month = context["previous_month"]
        context["previous_month_url"] = self.get_month_url(previous_month.year, previous_month.month)

        # 次月へのリンク
        next_month = context["next_month"]
        if next_month:
            context["next_month_url"] = self.get_month_url(next_month.year, next_month.month)

        return context

    @staticmethod
    def summaries():
        return ()


class GenericYearArchiveView(
    ListViewPerspectiveMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, YearArchiveView
):
    year_format = "%Y"
    allow_empty = True
    date_field = "date"
    make_object_list = True
    template_name = "generic/generic_archive_year.html"

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset:
            raise ImproperlyConfigured("Viewに `model` または `queryset` が未定義です。")  # pragma: no cover

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.year_archive_navbar_links(extra_menu)

    def get_year_url(self, year):
        raise NotImplementedError("get_year_url(year) を再定義してください。")  # pragma: no cover

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 今年へのリンク
        this_year = context["year"]
        context["this_month_url"] = self.get_year_url(this_year.year)

        # 前年へのリンク(常にある)
        previous_year = context["previous_year"]
        context["previous_year_url"] = self.get_year_url(previous_year.year)

        # 次年へのリンク
        next_year = context["next_year"]
        if next_year:
            context["next_year_url"] = self.get_year_url(next_year.year)

        return context

    @staticmethod
    def summaries():
        raise NotImplementedError("summaries()を実装してください。")  # pragma: no cover


class GenericLatestMonthRedirectView(Auth0LoginRequiredMixin, RedirectView):
    model = None

    def __init__(self):
        super().__init__()

        if hasattr(self, "menu"):
            raise ImproperlyConfigured("GenericLatestMonthRedirectView は `menu` に未対応です。")  # pragma: no cover

    def get_month_url(self, year, month):
        raise NotImplementedError("get_month_url()を実装してください。")  # pragma: no cover

    def get_redirect_url(self, *args, **kwargs):
        """最新のレコード、あるいは今月に移動"""
        latest = self.model.objects.order_by("-date").first()
        if latest:
            year = latest.date.year
            month = latest.date.month
        else:
            today = local_today()
            year = today.year
            month = today.month

        return self.get_month_url(year, month)


class GenericLatestYearRedirectView(Auth0LoginRequiredMixin, RedirectView):
    model = None

    def __init__(self):
        super().__init__()

        if hasattr(self, "menu"):
            raise ImproperlyConfigured("GenericLatestYearRedirectView は `menu` に未対応です。")  # pragma: no cover

    def get_year_url(self, year):
        raise NotImplementedError("get_year_url()を実装してください。")  # pragma: no cover

    def get_redirect_url(self, *args, **kwargs):
        """最新のレコード、あるいは今月に移動"""
        latest = self.model.objects.order_by("-date").first()
        if latest:
            year = latest.date.year
        else:
            today = local_today()
            year = today.year

        return self.get_year_url(year)

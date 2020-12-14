from typing import Any, Dict, Optional, Type

from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.db import ProgrammingError, transaction
from django.forms.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, MonthArchiveView, UpdateView
from django.views.generic.base import RedirectView, TemplateView, View
from django_filters.views import FilterView

from apps.core.menu import CRUDLMenu, NavbarMixin
from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.datetime import local_today
from apps.libs.db.models import get_model_fields
from apps.libs.views_mixin import ObjectListNameMixin, ObjectNameMixin, SuccessUrlMixin, SupportNextUrlMixin


class GenericStatusUpdateView(Auth0LoginRequiredMixin, View):
    """ ステータスを更新するView """

    status_pk_kwarg = "status"
    status_class = None  # type: Optional[Type]
    model_class = None  # type: Optional[Type]
    success_url = None

    def post(self, request, pk, *args, **kwargs):
        status = self.request.POST.get(self.status_pk_kwarg, None)
        if not status:
            raise SuspiciousOperation("ステータスが渡されていません。")

        status = get_object_or_404(self.status_class, pk=status)
        item = get_object_or_404(self.model_class, pk=pk)
        item.status = status
        item.save()

        messages.success(request, f"{status}に変更しました。")
        return redirect(self.success_url)


class GenericListView(ObjectListNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    template_name = "generic/generic_list.html"
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset and not self.get_queryset:
            raise ProgrammingError("Viewに `model` または `queryset` または `get_queryset()` が未定義です。")

        if self.menu:
            self.navbar_links = self.menu.list_navbar_links()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context


class GenericChildListView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    template_name = "generic/generic_list.html"
    parent_model = None
    child_model = None
    parent_key = None

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset and not self.get_queryset:
            raise ProgrammingError("Viewに `model` または `queryset` または `get_queryset()` が未定義です。")

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.parent_object = self.parent_model.objects.get(id=kwargs["pk"])

    def get_queryset(self):
        kwargs = dict()
        kwargs[self.parent_key] = self.parent_object.id
        return self.child_model.objects.filter(**kwargs)

    def get_object_name(self):
        return self.parent_object.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context


class GenericTreeView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    template_name = "generic/generic_tree.html"

    def __init__(self):
        super().__init__()
        if not self.model:
            raise ProgrammingError("Viewに `model` が未定義です。")

        if not hasattr(self.model, "get_absolute_url"):
            raise ProgrammingError("モデルに `get_absolute_url` の実装が必要です。")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context


class GenericAddView(
    SupportNextUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, CreateView
):
    template_name = "generic/generic_form.html"
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()
        if self.menu:
            self.navbar_links = self.menu.list_navbar_links()

    def get_form_class(self):
        # fields, form_classがある場合はそちらを優先
        if self.fields or self.form_class:
            return super().get_form_class()

        # 両方ないときはモデルを元に決める
        self.fields = get_model_fields(self.model)
        return super().get_form_class()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, f"{self.get_object_name()}を追加しました。")
        return response


class GenericEditView(
    SupportNextUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, UpdateView
):
    template_name = "generic/generic_form.html"
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()
        if self.menu:
            self.navbar_links = self.menu.list_navbar_links()

    def get_form_class(self):
        # fields, form_classがある場合はそちらを優先
        if self.fields or self.form_class:
            return super().get_form_class()

        # 両方ないときはモデルを元に決める
        self.fields = get_model_fields(self.model)
        return super().get_form_class()

    @staticmethod
    def get_extra_buttons():
        return ()

    @staticmethod
    def get_head_info_list():
        return ()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        context["extra_buttons"] = self.get_extra_buttons()
        context["head_info_list"] = self.get_head_info_list()
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, f"{self.get_object_name()}を更新しました。")
        return response


class GenericDetailView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, DetailView):
    template_name = "generic/generic_detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context


class GenericDeleteListView(SupportNextUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    success_url = None
    template_name = "generic/generic_delete_list.html"
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()
        if self.menu:
            self.navbar_links = self.menu.list_navbar_links()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def get_queryset(self):
        raise NotImplementedError("get_querysetを再定義してください。")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs.delete()
        messages.info(self.request, self.get_object_name() + "を一括削除しました。")
        return redirect(self.success_url)


class GenericDeleteView(
    SupportNextUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, DeleteView
):
    template_name = "generic/generic_delete.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"{self.get_object_name()}を削除しました。")
        return response


class GenericModelFormsetEditView(Auth0LoginRequiredMixin, NavbarMixin, FormView):
    template_name = "generic/generic_modelformset_edit.html"
    object_name = None
    success_message = None

    def __init__(self):
        super().__init__()
        if not self.object_name:
            raise ProgrammingError("Viewに `object_name` が未定義です。")

        if not self.success_message:
            raise ProgrammingError("Viewに `success_message` が未定義です。")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # "form" => "formset" にリネーム
        context["formset"] = context["form"]
        del context["form"]

        # object_nameを追加(タイトルで使われる)
        if "object_name" not in context:
            context["object_name"] = self.object_name

        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # フォームセットの保存
        form.save()

        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class GenericInlineFormsetView(Auth0LoginRequiredMixin, NavbarMixin, FormView):
    template_name = "generic/generic_inlineformset.html"
    object_name = None
    formset_class = None

    def __init__(self):
        super().__init__()
        if not self.object_name:
            raise ProgrammingError("Viewに `object_name` が未定義です。")

    def get_formset(self):
        return self.formset_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()

        if "formset" not in kwargs:
            kwargs["formset"] = self.get_formset()

        # object_nameを追加(タイトルで使われる)
        if "object_name" not in kwargs:
            kwargs["object_name"] = self.object_name

        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.get_formset()

        # 必ず両方の is_valid() を実行する
        is_form_valid = form.is_valid()
        is_formset_valid = formset.is_valid()

        if is_form_valid and is_formset_valid:
            return self.form_and_formset_valid(form, formset)
        else:
            return self.form_or_formset_invalid(form, formset)

    def form_and_formset_valid(self, form: BaseForm, formset) -> HttpResponse:
        with transaction.atomic():
            form.save()
            formset.instance = form.instance
            formset.save()

        messages.success(self.request, f"{self.object_name}を追加しました。")
        return super().form_valid(form)

    def form_or_formset_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class GenericSelectView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, FormView):
    select_kwargs = None
    template_name = "generic/generic_select_form.html"

    def __init__(self):
        super().__init__()
        if not self.form_class:
            raise ProgrammingError("Viewに `form_class` が未定義です。")

        if not self.select_kwargs:
            raise ProgrammingError("Viewに `select_kwargs` が未定義です。")

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def get_redirect_url(self, args) -> str:
        raise NotImplementedError("get_redirect_urlを再定義してください。")

    def form_valid(self, form):
        select = form.cleaned_data[self.select_kwargs]
        redirect_url = self.get_redirect_url(args=[select.pk])
        return HttpResponseRedirect(redirect_url)


class GenericTemplateView(Auth0LoginRequiredMixin, NavbarMixin, TemplateView):
    pass


class GenericMonthArchiveView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, MonthArchiveView):
    month_format = "%m"
    allow_empty = True
    date_field = "date"
    template_name = "generic/generic_archive_month.html"
    menu: CRUDLMenu = None

    def __init__(self):
        super().__init__()
        if not self.model and not self.queryset:
            raise ProgrammingError("Viewに `model` または `queryset` が未定義です。")

        if self.menu:
            self.navbar_links = self.menu.list_navbar_links()

    def get_month_url(self, year, month):
        return ""

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()

        # 前月へのリンク
        previous_month = context["previous_month"]
        if previous_month:
            context["previous_month_url"] = self.get_month_url(previous_month.year, previous_month.month)

        # 次月へのリンク
        next_month = context["next_month"]
        if next_month:
            context["next_month_url"] = self.get_month_url(next_month.year, next_month.month)

        return context

    @staticmethod
    def summaries():
        return ()


class GenericFilterView(Auth0LoginRequiredMixin, NavbarMixin, FilterView):
    template_name = "generic/generic_filter.html"


class GenericRedirectView(Auth0LoginRequiredMixin, NavbarMixin, RedirectView):
    pass


class GenericView(Auth0LoginRequiredMixin, View):
    pass


class GenericActionView(Auth0LoginRequiredMixin, View):
    """特定のモデルのインスタンスに対して操作を行うためのView"""

    model = None

    def action(self, instance):
        raise NotImplementedError("actionを再定義してください。")

    def get_success_url(self, instance):
        raise NotImplementedError("get_success_urlを再定義してください。")

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(self.model, pk=self.kwargs["pk"])
        self.action(instance)

        return self.get_success_url(instance)


class GenericLatestMonthRedirectView(Auth0LoginRequiredMixin, RedirectView):
    model = None

    def get_month_url(self, year, month):
        raise NotImplementedError("get_month_url()を実装してください。")

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

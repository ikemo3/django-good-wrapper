from typing import Optional, Type

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import IntegerChoices, Model, ProtectedError
from django.forms import BaseFormSet, Form, formset_factory
from django.forms.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView
from django.views.generic.base import View

from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.db.models import get_model_fields
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.views.multiple import MultipleFormView
from apps.libs.views_mixin import ObjectNameMixin, SuccessUrlMixin, SupportSuccessUrlMixin


class GenericFormView(Auth0LoginRequiredMixin, NavbarMixin, FormView):
    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        raise ImproperlyConfigured("GenericFormViewにmenuは定義しないでください。")  # pragma: no cover


class GenericBulkFormView(SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, FormView):
    template_name = "generic/generic_form.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.bulk_add_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = f"{self.get_object_name()}を一括追加"
        context["object_name"] = self.get_object_name()
        return context


class GenericBulkAddWithCommonFormView(
    ObjectNameMixin, SuccessUrlMixin, Auth0LoginRequiredMixin, NavbarMixin, MultipleFormView
):
    common_form_class = None
    form_class = None
    template_name = "generic/generic_bulk_add.html"

    def __init__(self):
        super().__init__()

        formset_class = formset_factory(form=self.form_class, extra=1)
        self.form_classes = (("common", self.common_form_class), ("formset", formset_class))

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.add_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = f"{self.get_object_name()}を一括追加"
        context["object_name"] = self.get_object_name()

        forms = context["forms"]
        context["form"] = forms[0]
        context["formset"] = forms[1]
        return context

    def form_and_formset_valid(self, form, formset):
        raise NotImplementedError("form_and_formset_valid(form, formset)を実装してください。")  # pragma: no cover

    def forms_valid(self, forms):
        form = forms[0]  # type: Form
        formset = forms[1]  # type: BaseFormSet

        self.form_and_formset_valid(form, formset)

        messages.success(self.request, f"{self.get_object_name()}を一括追加しました。")

        return super().forms_valid(forms)


class GenericAddView(
    SupportSuccessUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, CreateView
):
    template_name = "generic/generic_form.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.add_navbar_links(extra_menu)

    def get_initial(self):
        initial = super().get_initial()

        request_get = self.request.GET  # type: QueryDict

        for key, value in request_get.items():
            if key == "id":
                continue

            initial[key] = value

        return initial

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = f"{self.get_object_name()}を追加"
        context["object_name"] = self.get_object_name()
        context["extra_buttons"] = self.get_extra_buttons()
        context["submit_label"] = "追加"
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, f"{self.get_object_name()}を追加しました。")
        return response


class GenericEditView(
    SupportSuccessUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, UpdateView
):
    template_name = "generic/generic_form.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.edit_navbar_links(extra_menu)

    def get_form_class(self):
        # fields, form_classがある場合はそちらを優先
        if self.fields or self.form_class:
            return super().get_form_class()

        # 両方ないときはモデルを元に決める
        self.fields = get_model_fields(self.model)
        return super().get_form_class()

    def get_extra_buttons(self):
        if hasattr(self.object, "get_edit_actions"):
            return self.object.get_edit_actions()
        else:
            return ()

    @staticmethod
    def get_head_info_list():
        return ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = f"{self.get_object_name()}を編集"
        context["object_name"] = self.get_object_name()
        context["extra_buttons"] = self.get_extra_buttons()
        context["head_info_list"] = self.get_head_info_list()
        context["submit_label"] = "更新"
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, f"{self.get_object_name()}を更新しました。")
        return response


class GenericStatusUpdateView(SupportSuccessUrlMixin, SuccessUrlMixin, Auth0LoginRequiredMixin, View):
    """ステータスを更新するView"""

    status_class = None  # type: Type[IntegerChoices]
    model = None  # type: Optional[Type]
    success_url = None

    def __init__(self):
        super().__init__()
        if not self.status_class:
            raise ImproperlyConfigured("`status_class`(ステータスを表すIntegerChoices)が未定義です。")  # pragma: no cover

        if not self.model:
            raise ImproperlyConfigured("`model`が未定義です。")  # pragma: no cover

    def update_status(self, item, status):
        item.status = status
        item.save()

    def post(self, request, pk, status_id, *args, **kwargs):
        status = self.status_class(status_id)
        item = get_object_or_404(self.model, pk=pk)
        self.update_status(item, status)

        messages.success(request, f"{status.label}に変更しました。")

        return HttpResponseRedirect(self.get_success_url())


class GenericDeleteListView(SupportSuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, ListView):
    success_url = None
    template_name = "generic/generic_delete_list.html"

    def __init__(self):
        super().__init__()

        if not self.success_url:
            raise ImproperlyConfigured("`success_url`が未定義です。")  # pragma: no cover

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.delete_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def get_queryset(self):
        raise NotImplementedError("get_querysetを再定義してください。")  # pragma: no cover

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs.delete()
        messages.info(self.request, self.get_object_name() + "を一括削除しました。")
        return redirect(self.success_url)


class GenericDeleteView(
    SupportSuccessUrlMixin, SuccessUrlMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, DeleteView
):
    success_url = None
    template_name = "generic/generic_delete.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.delete_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        context["object_name"] = self.get_object_name()
        return context

    def delete(self, request, *args, **kwargs):
        def collect_model_names(protected_objects):
            names = set()
            for protected_object in protected_objects:  # type: Model
                names.add(protected_object._meta.verbose_name)

            return names

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f"{self.get_object_name()}を削除しました。")
            return response
        except ProtectedError as e:
            protected_models = "、".join(collect_model_names(e.protected_objects))
            message = f"削除できませんでした。『{protected_models}』にこの{self.get_object_name()}に依存するレコードがあります。"
            messages.error(self.request, message)
            return self.render_to_response(self.get_context_data(object=self.object))


class GenericSortView(ObjectNameMixin, SuccessUrlMixin, Auth0LoginRequiredMixin, NavbarMixin, FormView):
    template_name = "generic/generic_sort.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.sort_navbar_links(extra_menu)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # "form" => "formset" にリネーム
        context["formset"] = context["form"]
        del context["form"]

        context["title"] = f"{self.get_object_name()}をソート"
        context["object_name"] = self.get_object_name()

        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # フォームセットの保存
        form.save()

        messages.success(self.request, f"{self.get_object_name()}をソートしました。")
        return super().form_valid(form)


class GenericInlineFormsetView(ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, FormView):
    template_name = "generic/generic_inlineformset.html"
    object_name = None
    formset_class = None

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.formset_navbar_links(extra_menu)

    def get_formset(self):
        return self.formset_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["form"] = self.get_form()
        context["formset"] = self.get_formset()
        context["title"] = f"{self.get_object_name()}を追加"
        context["object_name"] = self.get_object_name()

        return context

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

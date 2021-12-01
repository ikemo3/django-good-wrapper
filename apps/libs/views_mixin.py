from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import Resolver404, resolve

from apps.libs.url import remove_query_string


class ObjectNameMixin:
    object_label = None
    model = None

    def get_object_name(self):
        if self.object_label:
            return self.object_label
        elif self.model:
            # noinspection PyProtectedMember
            return self.model._meta.verbose_name
        else:
            return "未設定"  # pragma: no cover


class ObjectListNameMixin:
    object_label = None
    model = None

    def get_object_name(self):
        if self.object_label:
            return self.object_label
        elif self.model:
            # noinspection PyProtectedMember
            return self.model._meta.verbose_name + "一覧"
        else:
            return "未設定"  # pragma: no cover


class TotalMixin:
    def get_total(self, field_name):
        # noinspection PyUnresolvedReferences
        return self.object_list.aggregate(Sum(field_name))[field_name + "__sum"] or 0


class CopyMixin:
    src_id_kwarg = "src_id"
    src_model = None
    copy_fields = None

    def get_source_object(self):
        if not self.src_model:
            raise ImproperlyConfigured("`src_model`(コピー元のモデルクラス)が未定義です。")  # pragma: no cover

        # noinspection PyUnresolvedReferences
        src_id = self.kwargs[self.src_id_kwarg]
        src = get_object_or_404(self.src_model, pk=src_id)
        return src

    def get_initial(self):
        # noinspection PyUnresolvedReferences
        initial = super().get_initial()
        src = self.get_source_object()

        if not self.copy_fields:
            raise ImproperlyConfigured("`copy_fields`(コピーするフィールド)が未定義です。")  # pragma: no cover

        if isinstance(self.copy_fields, str):
            raise ImproperlyConfigured(
                "`copy_fields`(コピーするフィールド)は文字列ではなく、tuple, list, dictを指定してください。"
            )  # pragma: no cover

        # フィールドのコピー
        if isinstance(self.copy_fields, dict):
            # dictの場合
            for src_field_name, field_name in self.copy_fields.items():
                if src_field_name == "self":
                    initial[field_name] = src
                else:
                    initial[field_name] = getattr(src, src_field_name)
        else:
            # tuple, listの場合
            for field_name in self.copy_fields:
                initial[field_name] = getattr(src, field_name)

        return initial


class MoveMixin(CopyMixin):
    @transaction.atomic
    def form_valid(self, form):
        # noinspection PyUnresolvedReferences
        response = super().form_valid(form)

        # 元のインスタンスを削除
        source = self.get_source_object()
        source.delete()

        return response


class SuccessUrlMixin:
    """追加・編集・削除が成功したときの戻り先を決定するためのmixin"""

    # noinspection PyUnresolvedReferences
    def get_success_url(self):
        # success_urlがある場合はそちらを優先
        if self.success_url:
            return super().get_success_url()

        # モデルに get_model_top_url がある場合はそれを呼ぶ
        if self.model and hasattr(self.model, "get_model_top_url"):
            return self.model.get_model_top_url()

        # モデルに get_list_url がある場合はそれを呼ぶ
        if self.model and hasattr(self.model, "get_list_url"):
            return self.model.get_list_url()

        raise ImproperlyConfigured(
            f"リダイレクト先が未指定です。success_urlを定義するか、モデル({self.model})にget_list_url()を定義してください。"
        )  # pragma: no cover


class SupportSuccessUrlMixin:
    # noinspection PyUnresolvedReferences
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["success_url"] = self.request.GET.get("next")
        return context

    def get_success_url(self):
        # noinspection PyUnresolvedReferences
        next_param = self.request.POST.get("success_url")

        try:
            # 解決できるパスかどうかのチェック
            resolve(remove_query_string(next_param))

            # 解決できるパスの場合はそのまま返す
            return next_param
        except Resolver404:
            # 解決できないパスの場合はデフォルトに任せる
            # noinspection PyUnresolvedReferences
            return super().get_success_url()


class SupportNextUrlMixin:
    def get_redirect_url(self):
        # noinspection PyUnresolvedReferences
        next_param = self.request.POST.get("next")

        try:
            # 解決できるパスかどうかのチェック
            resolve(next_param)

            # 解決できるパスの場合はそのまま返す
            return next_param
        except Resolver404:
            # 解決できないパスの場合はデフォルトに任せる
            # noinspection PyUnresolvedReferences
            return super().get_redirect_url()


class DisplayAsTableMixin:
    @staticmethod
    def display_as():
        return "table"

    @staticmethod
    def headers():
        raise NotImplementedError("headers()を定義してください")  # pragma: no cover

    @staticmethod
    def columns(instance):
        raise NotImplementedError("columns(self, instance)を定義してください")  # pragma: no cover

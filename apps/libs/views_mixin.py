from django.core.exceptions import ImproperlyConfigured
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import Resolver404, resolve


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
            return "未設定"


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
            return "未設定"


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
            raise ImproperlyConfigured("`src_model`(コピー元のモデルクラス)が未定義です。")

        # noinspection PyUnresolvedReferences
        src_id = self.kwargs[self.src_id_kwarg]
        src = get_object_or_404(self.src_model, pk=src_id)
        return src

    def get_initial(self):
        # noinspection PyUnresolvedReferences
        initial = super().get_initial()
        src = self.get_source_object()

        if not self.copy_fields:
            raise ImproperlyConfigured("`copy_fields`(コピーするフィールド)が未定義です。")

        # フィールドのコピー
        for field_name in self.copy_fields:
            initial[field_name] = getattr(src, field_name)

        return initial


class SuccessUrlMixin:
    # noinspection PyUnresolvedReferences
    def get_success_url(self):
        # success_urlがある場合はそちらを優先
        if self.success_url:
            return super().get_success_url()

        # モデルに get_list_url がある場合はそれを呼ぶ
        if self.model and hasattr(self.model, "get_list_url"):
            return self.model.get_list_url()

        # form_classがあって、そのMetaのmodelの get_list_url がある場合はそれを呼ぶ
        if hasattr(self, "form_class"):
            # noinspection PyProtectedMember
            model = self.form_class._meta.model
            if hasattr(model, "get_list_url"):
                return model.get_list_url()

        # 既存処理にフォールバック
        return super().get_success_url()


class SupportNextUrlMixin:
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
            resolve(next_param)

            # 解決できるパスの場合はそのまま返す
            return next_param
        except Resolver404:
            # 解決できないパスの場合はデフォルトに任せる
            # noinspection PyUnresolvedReferences
            return super().get_success_url()

from dataclasses import dataclass
from typing import List, Optional

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import BooleanField, CharField, ForeignKey, IntegerField
from django.views.generic.base import ContextMixin


@dataclass
class Perspective:
    key: str
    object_name: str
    type: str
    manager: models.Manager = None


@dataclass
class ListPerspective(Perspective):
    type: str = "list"


@dataclass
class SortPerspective(Perspective):
    type: str = "list"
    order_by: str = ""


@dataclass
class GroupingPerspective(Perspective):
    type: str = "grouping"
    group_by: str = ""


@dataclass
class RelatedPerspective(Perspective):
    type: str = "grouping"
    accessor: str = ""


class ListViewPerspectiveMixin(ContextMixin):
    model = None
    default_perspective_key = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        # perspectiveが指定されている場合はquerysetを上書き
        perspective = self.get_perspective()
        if isinstance(perspective, ListPerspective):
            self.queryset = perspective.manager.all()
        elif isinstance(perspective, SortPerspective):
            self.queryset = self.model.objects.order_by(perspective.order_by)

    def get_perspectives(self) -> List[Perspective]:
        return self.get_list_perspectives(self.model)

    def get_perspective(self) -> Optional[Perspective]:
        perspectives = self.get_perspectives()

        # perspective未対応のときはNone
        if not perspectives:
            return None

        # noinspection PyUnresolvedReferences
        perspective_key = self.request.GET.get("perspective") or self.default_perspective_key or "_default"

        for perspective in perspectives:
            if perspective.key == perspective_key:
                return perspective

        return None

    def get_context_data(self, **kwargs):
        # デフォルトのパースペクティブ(パラメータ"_default"、モデルのverbose_nameを使用)を先頭に追加
        default_perspective = Perspective(key="_default", type="list", object_name=self.get_object_name())

        context = super().get_context_data(**kwargs)

        # object_nameを追加(タイトルで使われる)
        # パースペクティブを最優先
        perspective = self.get_perspective()
        if perspective:
            context["object_name"] = perspective.object_name
        else:
            context["object_name"] = self.get_object_name()

        # 自分自身のパースペクティブを除く
        other_perspectives = list(self.get_perspectives())
        other_perspectives.insert(0, default_perspective)
        perspective = self.get_perspective()
        if perspective:
            other_perspectives.remove(perspective)
        else:
            other_perspectives.remove(default_perspective)

        context["other_perspectives"] = other_perspectives

        return context

    def display_as(self):
        perspective = self.get_perspective()
        if perspective:
            return perspective.type
        else:
            return "list"

    def group_by(self):
        perspective = self.get_perspective()
        if isinstance(perspective, GroupingPerspective):
            return perspective.group_by
        else:
            raise ImproperlyConfigured("GroupingPerspective 以外で `group_by` を呼び出そうとしています。")  # pragma: no cover

    @staticmethod
    def get_list_perspectives(cls):
        perspectives = []

        fields = cls._meta.fields
        for field in fields:
            if isinstance(field, ForeignKey) and not field.remote_field.parent_link:
                # 外部キーかつ親へのリンクを除く
                perspective = GroupingPerspective(
                    key=field.name, group_by=field.name, object_name=f"{field.verbose_name}別一覧"
                )
                perspectives.append(perspective)
            elif isinstance(field, IntegerField) and hasattr(field, "choices") and field.choices:
                perspective = GroupingPerspective(
                    key=field.name, group_by=field.name, object_name=f"{field.verbose_name}別一覧"
                )
                perspectives.append(perspective)
            elif isinstance(field, BooleanField):
                perspective = GroupingPerspective(
                    key=field.name, group_by=field.name, object_name=f"{field.verbose_name}別一覧"
                )
                perspectives.append(perspective)
            elif isinstance(field, CharField) and field.max_length <= 100:
                # 100文字以下の文字列はソート対象(100文字を超えると備考とかになるため)
                perspective = SortPerspective(
                    key=field.name, order_by=field.name, object_name=f"{field.verbose_name}でソート"
                )
                perspectives.append(perspective)

        return perspectives


class DetailViewPerspectiveMixin(ContextMixin):
    perspectives: List[RelatedPerspective] = []
    default_perspective_key = None

    def setup(self, request, *args, **kwargs):
        # noinspection PyUnresolvedReferences
        super().setup(request, *args, **kwargs)

    def get_perspectives(self) -> List[RelatedPerspective]:
        raise NotImplementedError("get_perspectives()を実装してください。")  # pragma: no cover

    def get_perspective(self) -> Optional[RelatedPerspective]:
        perspectives = self.get_perspectives()

        # noinspection PyUnresolvedReferences
        perspective_key = self.request.GET.get("perspective") or self.default_perspective_key or "_default"

        for perspective in perspectives:
            if perspective.key == perspective_key:
                return perspective

        return None

    def get_context_data(self, **kwargs):
        # デフォルトのパースペクティブ(パラメータ"_default"、モデルのverbose_nameを使用)を先頭に追加
        # noinspection PyUnresolvedReferences
        default_perspective = Perspective(key="_default", type="list", object_name=self.get_object_name())

        context = super().get_context_data(**kwargs)

        # 自分自身のパースペクティブを除く
        other_perspectives = list(self.get_perspectives())
        other_perspectives.insert(0, default_perspective)
        perspective = self.get_perspective()
        if perspective:
            other_perspectives.remove(perspective)
        else:
            other_perspectives.remove(default_perspective)

        context["other_perspectives"] = other_perspectives

        return context

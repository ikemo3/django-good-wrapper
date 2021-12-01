from typing import List, Union

from django.db.models import ForeignKey, ManyToManyRel, ManyToOneRel
from django.views.generic import DetailView

from apps.libs.auth.mixins import Auth0LoginRequiredMixin
from apps.libs.menu import CRUDLMenu, NavbarMixin
from apps.libs.perspective import DetailViewPerspectiveMixin, Perspective, RelatedPerspective
from apps.libs.views_mixin import ObjectNameMixin


class GenericDetailView(DetailViewPerspectiveMixin, ObjectNameMixin, Auth0LoginRequiredMixin, NavbarMixin, DetailView):
    template_name = "generic/generic_detail.html"

    @staticmethod
    def default_navbar_links(menu: CRUDLMenu, extra_menu):
        return menu.detail_navbar_links(extra_menu)

    def get_perspectives(self) -> List[Perspective]:
        return self.get_detail_perspectives(self.model)

    @staticmethod
    def get_extra_buttons():
        return ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = self.get_object()
        # object_nameを追加(タイトルで使われる)
        # パースペクティブを最優先
        perspective = self.get_perspective()  # type: RelatedPerspective
        if perspective:
            context["object_list_name"] = perspective.object_name
            context["object_list"] = getattr(obj, perspective.accessor).all()
            context["object_name"] = perspective.object_name
        else:
            context["object_name"] = self.get_object_name()

        context["extra_buttons"] = self.get_extra_buttons()
        return context

    @staticmethod
    def get_detail_perspectives(cls) -> List[RelatedPerspective]:
        perspectives = []

        fields = cls._meta.get_fields()
        for field in fields:  # type: Union[ManyToOneRel, ManyToManyRel]
            # 逆参照かつ親へのリンクを持たない(子モデルでない)場合
            if isinstance(field, (ManyToOneRel, ManyToManyRel)) and not field.parent_link:
                remote_field = field.remote_field  # type: ForeignKey
                remote_model = remote_field.model
                perspective = RelatedPerspective(
                    key=field.name,
                    accessor=field.get_accessor_name(),
                    object_name=f"{remote_model._meta.verbose_name}一覧",
                )
                perspectives.append(perspective)
            else:  # pragma: no cover
                # 逆参照以外は無視
                pass

        return perspectives

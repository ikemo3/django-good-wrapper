from typing import List

from django.urls import reverse

from apps.libs.inconsistency import Inconsistency


class CRUDLMixin:
    url_prefix = None

    @classmethod
    def get_list_url(cls):
        return reverse(cls.url_prefix + ":list")

    @classmethod
    def get_add_url(cls):
        return reverse(cls.url_prefix + ":add")

    def get_edit_url(self):
        # noinspection PyUnresolvedReferences
        return reverse(self.url_prefix + ":edit", args=[self.id])

    def get_delete_url(self):
        # noinspection PyUnresolvedReferences
        return reverse(self.url_prefix + ":delete", args=[self.id])

    def get_absolute_url(self):
        # noinspection PyUnresolvedReferences
        return reverse(self.url_prefix + ":detail", args=[self.id])

    def get_default_url(self):
        return self.get_absolute_url()


class InconsistenciesMixin:
    @staticmethod
    def get_inconsistencies() -> List[Inconsistency]:
        return []

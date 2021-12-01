from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model


class ActionIcon(Enum):
    ADD = "plus-circle"
    COPY = "copy"
    SEARCH = "search"


class ActionMixin:
    def get_edit_url(self):
        raise NotImplementedError(f"{self.__class__}にget_edit_url(self)を実装してください")  # pragma: no cover

    def get_default_url(self):
        raise NotImplementedError(f"{self.__class__}にget_default_url(self)を実装してください")  # pragma: no cover

    def get_edit_action(self):
        # noinspection PyTypeChecker
        return EditAction(instance=self)

    def get_actions(self):
        if hasattr(self, "get_copy_url"):
            # noinspection PyTypeChecker
            copy_action = CopyAction(instance=self)
            return [copy_action]
        else:
            return []


class NoActionMixin:
    @staticmethod
    def get_edit_url():
        return ""

    @staticmethod
    def get_default_url():
        return ""

    @staticmethod
    def get_actions():
        return []


@dataclass
class Action:
    @property
    def is_divider(self):
        return False


@dataclass
class PostAction(Action):
    label: str
    url: str

    @property
    def is_post(self):
        return True


@dataclass
class LinkAction(Action):
    label: str
    url: str


@dataclass
class AddAction(Action):
    url: str
    icon: str = ActionIcon.ADD
    label: str = "追加"


@dataclass
class BulkAddAction(Action):
    url: str
    label: str = "一括追加"


@dataclass
class SortAction(Action):
    url: str
    label: str = "ソート"


@dataclass
class SearchAction(Action):
    url: str
    icon: str = ActionIcon.SEARCH
    label: str = "検索"


@dataclass
class DetailAction(Action):
    instance: Model
    label: str = "詳細"

    @property
    def url(self):
        # noinspection PyUnresolvedReferences
        return self.instance.get_absolute_url()


@dataclass
class DeleteAction(Action):
    instance: Model
    label: str = "削除"
    is_danger = True

    @property
    def url(self):
        # noinspection PyUnresolvedReferences
        return self.instance.get_delete_url()


@dataclass
class EditAction(Action):
    instance: Model
    label: str = "編集"

    @property
    def url(self):
        # noinspection PyUnresolvedReferences
        return self.instance.get_edit_url()


@dataclass
class CopyAction(Action):
    instance: Model
    icon: str = ActionIcon.COPY
    label: str = "複製"

    @property
    def url(self):
        # noinspection PyUnresolvedReferences
        return self.instance.get_copy_url()


@dataclass
class DividerAction(Action):
    is_divider: bool = True


class ActionList(list):
    def __sub__(self, other):
        if not isinstance(other, Action):
            raise ImproperlyConfigured(f"Action以外は対応していません: {other}")  # pragma: no cover

        # URLが同じものを同じメニューとして扱う
        links = list(filter(lambda link: link.is_divider or link.url != other.url, self))
        return ActionList(tuple(links))

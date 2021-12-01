from dataclasses import dataclass
from typing import List, Optional, Sequence, Set, Tuple

from django.db.models import Manager

from apps.libs.actions import Action


@dataclass
class Inconsistency:
    instance: object
    reason: str
    fix_actions: Sequence[Action]


class OneToOneInconsistencyValidator:
    forward_manager: Manager = None
    forward_to_related_key: str = None
    reverse_manager: Manager = None
    reverse_to_related_key: str = None

    # noinspection PyProtectedMember
    def __init__(self):
        self.forward_model_name = self.forward_manager.model._meta.verbose_name
        self.reverse_model_name = self.reverse_manager.model._meta.verbose_name

        # 常に使用するものについて、select_relatedを自動でしておく
        self.forward_manager = self.forward_manager.select_related(self.forward_to_related_key)
        self.reverse_manager = self.reverse_manager.select_related(self.reverse_to_related_key)

    def get_forward_fix_action(self, instance) -> Action:
        """参照がないときの修正アクション"""
        raise NotImplementedError("get_forward_fix_action(self, instance)を実装してください")  # pragma: no cover

    def get_reverse_fix_action(self, related_instance) -> Action:
        """逆参照がないときの修正アクション"""
        raise NotImplementedError("get_reverse_fix_action(self, instance)を実装してください")  # pragma: no cover

    def check_instance(self, instance, related_instance) -> Optional[Inconsistency]:
        """インスタンスの中身をチェックするメソッド"""
        raise NotImplementedError("check_instance(self, instance, related_instance)を実装してください")  # pragma: no cover

    def validate(self) -> List[Inconsistency]:
        inconsistencies = []
        instance_pair_set: Set[Tuple] = set()

        # Forward -> Reverse
        for instance in self.forward_manager.all():
            # 参照先が存在しない場合
            inconsistency = self.validate_forward_inconsistency(instance)
            if inconsistency:
                inconsistencies.append(inconsistency)
            else:
                instance_pair_set.add((instance, getattr(instance, self.forward_to_related_key)))

        # Reverse -> Forward
        for instance in self.reverse_manager.all():
            inconsistency = self.validate_reverse_consistent(instance)
            if inconsistency:
                inconsistencies.append(inconsistency)
            else:
                instance_pair_set.add((getattr(instance, self.reverse_to_related_key), instance))

        for instance, related_instance in instance_pair_set:
            assert instance
            assert related_instance

            inconsistency = self.check_instance(instance, related_instance)
            if inconsistency:
                inconsistencies.append(inconsistency)

        return inconsistencies

    def validate_forward_inconsistency(self, instance) -> Optional[Inconsistency]:
        """参照の整合性チェック"""
        # ForeignKeyの存在チェック
        if not self.is_forward_consistent(instance):
            reason = f"{self.forward_model_name}に対応する{self.reverse_model_name}レコードが存在しません"
            return Inconsistency(instance=instance, reason=reason, fix_actions=[self.get_forward_fix_action(instance)])

        return None

    def is_forward_consistent(self, instance):
        """参照の整合性が取れているかどうか"""
        return getattr(instance, self.forward_to_related_key) is not None

    def validate_reverse_consistent(self, related_instance) -> Optional[Inconsistency]:
        """逆参照の整合性チェック"""
        if not self.is_reverse_consistent(related_instance):
            reason = f"{self.reverse_model_name}に対応する{self.forward_model_name}レコードが存在しません"
            return Inconsistency(
                instance=related_instance, reason=reason, fix_actions=[self.get_reverse_fix_action(related_instance)]
            )

        return None

    def is_reverse_consistent(self, related_instance):
        """逆参照の整合性が取れているかどうか"""
        return hasattr(related_instance, self.reverse_to_related_key)

from dataclasses import dataclass
from itertools import groupby
from typing import Optional, Type

from django import template
from django.db import models
from django.db.models import Field, Model, QuerySet
from django.template import RequestContext
from django.template.base import FilterExpression
from django.template.exceptions import TemplateSyntaxError

register = template.Library()


@register.tag
def grouping(parser, token):
    """regroupタグと以下の点を除いて同じ機能。
    ・3つ目の引数(グループ化するキー)は文字列ではなく、式として解釈される
    ・自動でソートされてからグループ化される
    """
    bits = token.split_contents()
    if len(bits) != 6:
        raise TemplateSyntaxError("'grouping' は5つの引数を持つ必要があります。")  # pragma: no cover
    if bits[2] != "by":
        raise TemplateSyntaxError("'grouping' の2つ目の引数は 'by' でなければなりません。")  # pragma: no cover
    if bits[4] != "as":
        raise TemplateSyntaxError("'grouping' の4つ目の引数は 'as' でなければなりません。")  # pragma: no cover

    target = parser.compile_filter(bits[1])
    var_name = bits[5]
    group_by_name = parser.compile_filter(bits[3])
    return GroupingNode(target, group_by_name, var_name)


@dataclass
class GroupResult:
    grouper: str
    list: list


class GroupingNode(template.Node):
    def __init__(self, target: FilterExpression, group_by_name: FilterExpression, var_name: str):
        self.target = target
        self.group_by_name = group_by_name
        self.var_name = var_name

    @staticmethod
    def get_attr(obj: models.Model, key):
        return getattr(obj, key)

    @staticmethod
    def get_model_class(object_list) -> Optional[Type[Model]]:
        if not object_list:
            return None

        return object_list[0].__class__

    @staticmethod
    def get_choice_label(model_class: Type[Model], attr_name, choice_key, values):
        # モデルフィールドでない場合は最初のインスタンスから取得
        if not hasattr(model_class, attr_name):
            instance = values[0]
            return getattr(instance, attr_name)

        field: Field = getattr(model_class, attr_name).field

        # choicesが存在しないまたは未指定のときはキー自体を返す
        if not hasattr(field, "choices") or not field.choices:
            return choice_key

        # choicesのどれにもマッチしない場合はキー自体を返す(通常はない)
        choice_list = list(filter(lambda c: c[0] == choice_key, field.choices))
        if not choice_list:
            return choice_key

        _, label = choice_list[0]
        return label

    def make_group_result(self, key, val, model_class: Type[Model], group_by_name):
        values = list(val)
        return GroupResult(grouper=self.get_choice_label(model_class, group_by_name, key, values), list=values)

    def render(self, context: RequestContext):
        # グループ化するキーの名前
        group_by_name = self.group_by_name.resolve(context, ignore_failures=True)

        # グループ化するオブジェクトのリスト(ソートしておく)
        object_list = self.target.resolve(context, ignore_failures=True)  # type: QuerySet

        # ソート
        current_order_by: tuple = object_list.query.order_by
        new_order_by = [group_by_name, *current_order_by]
        object_list = object_list.order_by(*new_order_by)

        model_class = self.get_model_class(object_list)

        # グループ化してcontextに詰める
        grouped_object_list = groupby(object_list, key=lambda obj: self.get_attr(obj, group_by_name))
        results = [self.make_group_result(key, val, model_class, group_by_name) for key, val in grouped_object_list]
        context[self.var_name] = results

        return ""

import pytest

from apps.libs.menu import Menu
from apps.libs.str import fqcn, is_int, split_first


@pytest.mark.parametrize(
    "value, expected",
    (
        ("1", True),
        ("-1", True),
        ("a", False),
    ),
)
def test_is_str(value, expected):
    assert is_int(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    (
        (str, "builtins.str"),
        ("abc", "builtins.str"),
        (Menu, "apps.libs.menu.Menu"),
        (Menu(submenus=[]), "apps.libs.menu.Menu"),
    ),
)
def test_fqcn(value, expected):
    assert fqcn(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    (
        ("🈳未着手", ("🈳", "未着手")),
        ("🏃‍♂️習慣", ("🏃‍♂️", "習慣")),
        ("あいう", ("あ", "いう")),
    ),
)
def test_split_first(value, expected):
    """最初の文字で分割する。絵文字の場合を考慮。"""
    assert split_first(value) == expected

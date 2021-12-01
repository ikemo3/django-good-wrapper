import pytest


@pytest.mark.parametrize(
    "text, prefix, expected",
    (
        ("abc", "a", True),
        ("abc", "b", False),
        (1, "a", False),
    ),
)
def test_do_startswith(text, prefix, expected):
    from apps.libs.templatetags import view

    assert view.do_startswith(text, prefix) is expected

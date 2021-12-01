from apps.libs.templatetags.debug import get_class


def test_get_class():
    assert get_class("") == str

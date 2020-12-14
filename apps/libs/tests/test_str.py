import pytest

from apps.libs.str import is_int


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

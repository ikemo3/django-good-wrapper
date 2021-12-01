import pytest

from apps.libs.collections import as_list


@pytest.mark.parametrize(
    "x, expected",
    (
        ([], []),
        ([1, 2, 3], [1, 2, 3]),
        ((), []),
        ((1, 2, 3), [1, 2, 3]),
        (1, [1]),
    ),
)
def test_as_list(x, expected):
    assert as_list(x) == expected

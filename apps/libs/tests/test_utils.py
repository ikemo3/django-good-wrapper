from datetime import datetime

import pytest

from apps.libs.tests.utils import freeze_time, prepare_inputs


def test_prepare_inputs():
    def f():
        return "x"

    data = dict(
        a=1,
        b="abc",
        c=f,
        d=[1, 2],
        e=[f, f],
    )

    prepared_data = prepare_inputs(data)

    assert prepared_data == dict(
        a=1,
        b="abc",
        c="x",
        d=[1, 2],
        e=["x", "x"],
    )


@pytest.mark.parametrize(
    "dt",
    (
        # タイムゾーンなし(日本時間)
        "2021-06-10 00:00:00",
        # タイムゾーンあり(GMT)
        "2021-06-09 15:00:00 GMT",
    ),
)
def test_freeze_time(dt):
    with freeze_time(dt):
        now = datetime.now()
        assert now == datetime(2021, 6, 10, 0, 0, 0)

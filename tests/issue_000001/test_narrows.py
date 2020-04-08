from typing import NamedTuple

import pendulum

from pytest import raises
from typefit import narrows, typefit


def test_date_time():
    assert narrows.DateTime("2019-01-01T00:00:00Z") == pendulum.parse(
        "2019-01-01T00:00:00Z"
    )

    with raises(ValueError):
        assert narrows.DateTime("xxx")


def test_date():
    assert narrows.Date("2019-01-01") == pendulum.parse("2019-01-01").date()

    with raises(ValueError):
        assert narrows.Date("xxx")


def test_timestamp():
    assert narrows.TimeStamp(1175714200) == pendulum.from_timestamp(1175714200)


def test_integration():
    class Foo(NamedTuple):
        date: narrows.DateTime

    assert typefit(Foo, {"date": "2019-01-01T00:00:00Z"}) == Foo(
        pendulum.parse("2019-01-01T00:00:00Z")
    )

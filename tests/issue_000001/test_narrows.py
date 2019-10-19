from typing import NamedTuple

import pendulum
from pytest import raises
from typefit import narrows, typefit


def test_date_time():
    assert narrows.DateTimeFit("2019-01-01T00:00:00Z") == pendulum.parse(
        "2019-01-01T00:00:00Z"
    )

    with raises(ValueError):
        assert narrows.DateTimeFit("xxx")


def test_date():
    assert narrows.DateFit("2019-01-01") == pendulum.parse("2019-01-01").date()

    with raises(ValueError):
        assert narrows.DateFit("xxx")


def test_timestamp():
    assert narrows.TimeStampFit(1175714200) == pendulum.from_timestamp(1175714200)


def test_integration():
    class Foo(NamedTuple):
        date: narrows.DateTimeFit

    assert typefit(Foo, {"date": "2019-01-01T00:00:00Z"}) == Foo(
        pendulum.parse("2019-01-01T00:00:00Z")
    )

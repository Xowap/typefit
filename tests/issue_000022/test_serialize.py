from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple
from uuid import uuid4

from pendulum import date, datetime

from typefit import meta, other_field, serialize, typefit
from typefit.serialize import SaneSerializer


def test_int():
    assert serialize(42) == 42


def test_bool():
    assert serialize(True) is True


def test_float():
    assert serialize(42.42) == 42.42


def test_str():
    assert serialize("hello") == "hello"


def test_none():
    assert serialize(None) is None


def test_typefit_serialize():
    class Foo:
        def __typefit_serialize__(self):
            return "foo"

    assert serialize(Foo()) == "foo"


def test_named_tuple():
    class Foo(NamedTuple):
        x: int
        y: int

    assert serialize(Foo(1, 2)) == {"x": 1, "y": 2}


def test_dataclass_simple():
    @dataclass
    class Foo:
        x: int
        y: int

    assert serialize(Foo(1, 2)) == {"x": 1, "y": 2}


def test_dataclass_source():
    @dataclass
    class Foo:
        x: int = field(metadata=meta(source=other_field("y")))

    assert serialize(Foo(42)) == {"y": 42}


def test_dataclass_recursive_simple():
    @dataclass
    class Bar:
        x: int

    @dataclass
    class Foo:
        x: Bar

    assert serialize(Foo(Bar(42))) == {"x": {"x": 42}}


def test_dataclass_recursive_source():
    @dataclass
    class Bar:
        x: int

    @dataclass
    class Foo:
        y: Bar = field(metadata=meta(source=other_field("x")))

    base = Foo(Bar(42))
    serialized = serialize(base)
    fit = typefit(Foo, serialized)

    assert serialized == {"x": {"x": 42}}
    assert fit == base


def test_uuid():
    u = uuid4()
    assert serialize(u) == f"{u}"


def test_datetime():
    d = datetime(2000, 1, 1, tz="UTC")
    assert serialize(d) == "2000-01-01T00:00:00+00:00"


def test_date():
    d = date(2000, 1, 1)
    assert serialize(d) == "2000-01-01"


def test_sequence():
    d = date(2000, 1, 1)
    assert serialize([d]) == ["2000-01-01"]
    assert serialize((d,)) == ["2000-01-01"]


def test_json():
    s = SaneSerializer()
    assert s.json(42) == "42"


def test_enum():
    class Test(Enum):
        a = "a"

    assert serialize(Test.a) == "a"


def test_int_string():
    class IntString(int):
        def __typefit_serialize__(self):
            return f"{self}"

    class Foo(NamedTuple):
        x: IntString

    assert serialize(Foo(IntString(42))) == {"x": "42"}

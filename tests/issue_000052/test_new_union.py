from dataclasses import dataclass

from typefit import typefit


@dataclass
class Foo:
    a: int


@dataclass
class Bar:
    b: str


def test_new_union():
    x = typefit(int | str | bool, 1)
    assert x == 1

    x = typefit(Foo | Bar, {"a": 1})
    assert x == Foo(1)

    x = typefit(Foo | Bar, {"b": "hello"})
    assert x == Bar("hello")

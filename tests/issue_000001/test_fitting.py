from typing import List, NamedTuple, Optional, Text, Union

from pytest import raises

from typefit.fitting import typefit


def test_handle_type():
    with raises(ValueError):
        assert typefit(int, "42") == 42

    assert typefit(float, 42) == 42.0

    with raises(ValueError):
        typefit(int, "xxx")

    class SomeType:
        def __init__(self, value: str):
            self.value = value

        def __eq__(self, other: "SomeType"):
            if not isinstance(other, self.__class__):
                return False

            return self.value == other.value

    assert typefit(SomeType, "foo") == SomeType("foo")


def test_typefit():
    assert typefit(int, 42) == 42

    with raises(ValueError):
        assert typefit(int, "42") == 42

    class Foo(NamedTuple):
        things: List[int]

    class Bar(NamedTuple):
        foo: Union[int, Foo]

    t1 = {"foo": 42}
    t2 = {"foo": {"things": [1, 2, 3]}}

    f1 = typefit(Bar, t1)
    f2 = typefit(Bar, t2)

    assert f1.foo == 42
    assert f2.foo.things == [1, 2, 3]


def test_handle_union():
    t = Union[int, str]
    assert typefit(t, 42) == 42
    assert typefit(t, "xxx") == "xxx"

    with raises(ValueError):
        typefit(Union[int, float], "xxx")


def test_handle_list():
    t = List[List[int]]
    v = [[1, 2, 3], [4, 5, 6]]

    assert typefit(t, v) == v

    with raises(ValueError):
        typefit(List, v)

    with raises(ValueError):
        typefit(Union, v)

    with raises(ValueError):
        typefit(t, 42)


def test_named_tuple():
    class Foo(NamedTuple):
        a: int
        b: Text

    assert typefit(Foo, {"a": 42, "b": "hello"}) == Foo(42, "hello")

    with raises(ValueError):
        typefit(None, {})

    with raises(ValueError):
        typefit(Foo, None)


def test_handle_none():
    assert typefit(None, None) is None
    assert typefit(None.__class__, None) is None


def test_none():
    class NoneType(NamedTuple):
        foo: None

    assert typefit(None, None) is None
    assert typefit(List[None], [None]) == [None]
    assert typefit(NoneType, {"foo": None}) == NoneType(None)
    assert typefit(Optional[int], None) is None
    assert typefit(List[Optional[int]], [0, 1, 2, None]) == [0, 1, 2, None]


def test_bool():
    assert typefit(List[Union[int, bool]], [1, True, 0, False]) == [1, True, 0, False]

from typing import List, NamedTuple, Optional, Text, Union

from pytest import raises

from typefit.fitting import (
    _handle,
    _handle_list,
    _handle_mappings,
    _handle_none,
    _handle_type,
    _handle_union,
    typefit,
)


def test_handle_type():
    with raises(ValueError):
        assert _handle_type(int, "42") == 42

    assert _handle_type(float, 42) == 42.0

    with raises(ValueError):
        _handle_type(int, "xxx")

    class SomeType:
        def __init__(self, value: str):
            self.value = value

        def __eq__(self, other: "SomeType"):
            if not isinstance(other, self.__class__):
                return False

            return self.value == other.value

    assert _handle_type(SomeType, "foo") == SomeType("foo")


def test_handle():
    def h_yes(t, value):
        return value

    def h_no(t, value):
        raise ValueError

    assert _handle([h_no, h_no, h_yes], int, 42) == 42

    with raises(ValueError):
        _handle([h_no, h_no], int, "xxx")


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
    assert _handle_union(t, 42) == 42
    assert _handle_union(t, "xxx") == "xxx"

    with raises(ValueError):
        _handle_union(Union[int, float], "xxx")


def test_handle_list():
    t = List[List[int]]
    v = [[1, 2, 3], [4, 5, 6]]

    assert _handle_list(t, v) == v

    with raises(ValueError):
        _handle_list(List, v)

    with raises(ValueError):
        _handle_list(Union, v)

    with raises(ValueError):
        _handle_list(t, 42)


def test_named_tuple():
    class Foo(NamedTuple):
        a: int
        b: Text

    assert _handle_mappings(Foo, {"a": 42, "b": "hello"}) == Foo(42, "hello")

    with raises(ValueError):
        _handle_mappings(None, {})

    with raises(ValueError):
        _handle_mappings(Foo, None)


def test_handle_none():
    assert _handle_none(None, None) is None
    assert _handle_none(None.__class__, None) is None


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

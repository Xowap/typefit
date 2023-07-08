from typing import Literal, NamedTuple, Union

from pytest import raises

from typefit import typefit


def test_handle_literal():
    t = Literal["a", "b", "c"]
    assert typefit(t, "a") == "a"
    assert typefit(t, "b") == "b"
    assert typefit(t, "c") == "c"

    with raises(ValueError):
        typefit(t, "d")


def test_typefit():
    class A(NamedTuple):
        type: Literal["a"]

    class B(NamedTuple):
        type: Literal["b"]

    T = Union[A, B]  # noqa

    assert isinstance(typefit(T, {"type": "a"}), A)
    assert isinstance(typefit(T, {"type": "b"}), B)

    with raises(ValueError):
        typefit(T, {"type": "c"})

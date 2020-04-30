from dataclasses import dataclass
from typing import Any, List, Text, Type, TypeVar, Union

from typefit import Fitter
from typefit.nodes import Node
from typefit.reporting import PrettyJson5Formatter

T = TypeVar("T")


def to_fit_node(t: Type[T], v: Any) -> Node:
    f = Fitter()
    node = f._as_node(v)

    try:
        f.fit_node(t, node)
    except ValueError:
        pass

    return node


def test_format_flat():
    node = to_fit_node(Union[bool, int], "42")
    assert (
        PrettyJson5Formatter().format(node)
        == """// Not a bool
// Not an int
// No matching type in Union
\"42\""""
    )


def test_format_mapping_wrong_key():
    @dataclass
    class Foo:
        x: int
        y: int

    node = to_fit_node(Foo, {"x": 42, "y": "42"})
    out = PrettyJson5Formatter().format(node)
    assert (
        out
        == """// Wrong keys set for 'tests.issue_000014.test_format.test_format_mapping_wrong_key.<locals>.Foo'. No fit for keys: 'y'
{
    "x": 42,

    // Not an int
    "y": "42",
}"""
    )


def test_format_mapping_not_mapping():
    @dataclass
    class Foo:
        x: int
        y: int

    node = to_fit_node(Foo, 42)
    out = PrettyJson5Formatter().format(node)
    assert (
        out
        == """// 'tests.issue_000014.test_format.test_format_mapping_not_mapping.<locals>.Foo' can only fit an object
42"""
    )


def test_format_list_partial():
    node = to_fit_node(List[int], [1, 2, 3, 4, 5, "6", 7, 8, 9, "10", 11, 12, 13])
    out = PrettyJson5Formatter().format(node)
    assert (
        out
        == """// Not all list items fit
[
    // Not an int
    "6",
]"""
    )


def test_list_of_foo():
    @dataclass
    class Foo:
        x: int
        y: Text

    @dataclass
    class Results:
        count: int
        results: List[Foo]

    node = to_fit_node(
        Results,
        {
            "count": 3,
            "results": [
                {"x": 42, "y": "foo"},
                {"x": 1337, "y": 1337},
                {"x": 421, "y": True},
            ],
        },
    )

    out = PrettyJson5Formatter().format(node)

    assert (
        out
        == """// Wrong keys set for 'tests.issue_000014.test_format.test_list_of_foo.<locals>.Results'. No fit for keys: 'results'
{
    "count": 3,

    // Not all list items fit
    "results": [
        // Wrong keys set for 'tests.issue_000014.test_format.test_list_of_foo.<locals>.Foo'. No fit for keys: 'y'
        {
            "x": 1337,

            // Not a string
            "y": 1337,
        },
    ],
}"""
    )

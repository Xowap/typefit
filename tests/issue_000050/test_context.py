from dataclasses import dataclass, field
from typing import Any, Mapping

from pytest import raises

from typefit import Fitter, PrettyJson5Formatter, meta, typefit
from typefit.nodes import Node
from typefit.reporting import ErrorReporter


@dataclass
class Child:
    value: int
    _root: "Root" = field(metadata=meta(inject_root=True))
    _foo: int = field(metadata=meta(context="foo"))


@dataclass
class Root:
    child: Child
    _foo: int = field(metadata=meta(context="foo"))


@dataclass
class B:
    val: int
    foo: Mapping[str, str] = field(metadata=meta(context="foo"))


@dataclass
class A:
    val: Mapping[str, Mapping[str, B]]


@dataclass
class DoubleFit:
    a: int = field(metadata=meta(context="a"))
    b: Any = field(metadata=meta(context="b"))


class TestErrorReporter(ErrorReporter):
    def __init__(self):
        self.formatter = PrettyJson5Formatter(colors="")
        self.error = ""

    def report(self, node: "Node") -> None:
        self.error = self.formatter.format(node)


def test_context_injection():
    x: Root = typefit(
        Root,
        dict(
            child=dict(
                value=42,
            ),
        ),
        context=dict(foo=42),
    )

    assert x.child.value == 42
    assert x.child._foo == 42
    assert x._foo == 42


def test_root_injection():
    x: Root = typefit(
        Root,
        dict(
            child=dict(
                value=42,
            ),
        ),
        context=dict(foo=42),
    )

    assert x.child._root is x


def test_context_mapping_injection():
    a: A = typefit(
        A,
        dict(
            val=dict(
                foo=dict(
                    bar=dict(
                        val=42,
                    )
                ),
            ),
        ),
        context=dict(foo=dict(hello="world")),
    )

    assert a.val["foo"]["bar"].val == 42
    assert a.val["foo"]["bar"].foo["hello"] == "world"


def test_context_injection_fail():
    rep = TestErrorReporter()
    fitter = Fitter(error_reporter=rep)

    with raises(ValueError):
        fitter.fit(
            Root,
            dict(
                child=dict(
                    value=42,
                ),
            ),
        )

    assert (
        rep.error
        == """// Wrong keys set for 'tests.issue_000050.test_context.Root'. No fit for keys: 'child'. Key 'foo' is missing from the context
{
    // Wrong keys set for 'tests.issue_000050.test_context.Child'. Key 'foo' is missing from the context
    "child": {
        "value": 42,
    },
}"""
    )


def test_double_fit():
    context = dict(a=1, b=2)
    x: DoubleFit = typefit(
        DoubleFit,
        dict(),
        context=context,
    )

    assert x.a == 1
    assert x.b == 2

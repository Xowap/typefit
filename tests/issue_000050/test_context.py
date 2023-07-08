from dataclasses import dataclass, field

from typefit import meta, typefit


@dataclass
class Child:
    value: int
    # _root: "Root" = field(metadata=meta(is_root=True))
    _foo: int = field(metadata=meta(context="foo"))


@dataclass
class Root:
    child: Child
    _foo: int = field(metadata=meta(context="foo"))


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
    # assert x.child._root is x
    assert x.child._foo == 42
    assert x._foo == 42

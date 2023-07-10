from dataclasses import dataclass, field

from typefit import meta, serialize, typefit


@dataclass
class Foo:
    a: int
    b: int = field(metadata=meta(context="foo"))


def test_serialize_injected():
    data = {"a": 42}
    x = typefit(Foo, data, context=dict(foo=42))
    assert serialize(x) == data

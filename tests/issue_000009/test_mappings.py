from dataclasses import dataclass

from typefit.fitting import typefit


def test_mappings():
    @dataclass
    class Foo:
        a: int
        b: str

    @dataclass
    class Bar(Foo):
        c: bool

    assert typefit(Bar, {"a": 42, "b": "42", "c": True}) == Bar(42, "42", True)

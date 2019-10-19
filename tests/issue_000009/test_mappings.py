from dataclasses import dataclass

from typefit.fitting import _handle_mappings


def test_mappings():
    @dataclass
    class Foo:
        a: int
        b: str

    @dataclass
    class Bar(Foo):
        c: bool

    assert _handle_mappings(Bar, {"a": 42, "b": "42", "c": True}) == Bar(42, "42", True)

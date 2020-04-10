from dataclasses import dataclass
from typing import Dict, List, Text

from pytest import fixture, raises
from typefit.fitting import Fitter, FlatNode, ListNode, MappingNode


@fixture(name="fitter")
def make_fitter():
    return Fitter()


def test_flat_node_success(fitter: Fitter):
    node = fitter._as_node(42)
    assert isinstance(node, FlatNode)
    assert fitter.fit_node(int, node) == 42
    assert node.fit_success


def test_flat_node_failure(fitter: Fitter):
    node = fitter._as_node("hello")
    assert isinstance(node, FlatNode)

    with raises(ValueError):
        fitter.fit_node(int, node)

    assert not node.fit_success


def test_list_node_success(fitter: Fitter):
    node = fitter._as_node([1, 2, 3])
    assert isinstance(node, ListNode)
    assert fitter.fit_node(List[int], node) == [1, 2, 3]
    assert node.fit_success


def test_list_node_failure(fitter: Fitter):
    node = fitter._as_node([1, 2, "foo"])
    assert isinstance(node, ListNode)

    with raises(ValueError):
        fitter.fit_node(List[int], node)

    assert not node.fit_success


def test_mapping_node_dict_success(fitter: Fitter):
    node = fitter._as_node({"a": 1, "b": 2})
    assert isinstance(node, MappingNode)
    assert fitter.fit_node(Dict[Text, int], node) == {"a": 1, "b": 2}
    assert node.fit_success


def test_mapping_node_dict_failure(fitter: Fitter):
    node = fitter._as_node({"a": 1, "b": "2"})
    assert isinstance(node, MappingNode)

    with raises(ValueError):
        fitter.fit_node(Dict[Text, int], node)

    assert not node.fit_success


def test_mapping_node_dataclass_success(fitter: Fitter):
    @dataclass
    class Foo:
        x: int
        y: int

    node = fitter._as_node({"x": 1, "y": 2})
    assert isinstance(node, MappingNode)
    assert fitter.fit_node(Foo, node) == Foo(1, 2)
    assert node.fit_success


def test_mapping_node_dataclass_missing_field(fitter: Fitter):
    @dataclass
    class Foo:
        x: int
        y: int

    node = fitter._as_node({"x": 1})
    assert isinstance(node, MappingNode)

    with raises(ValueError):
        fitter.fit_node(Foo, node)

    assert not node.fit_success
    assert node.missing_keys == ["y"]
    assert node.unwanted_keys == []


def test_mapping_node_dataclass_incorrect_field(fitter: Fitter):
    @dataclass
    class Foo:
        x: int
        y: int

    node = fitter._as_node({"x": 1, "y": "2"})
    assert isinstance(node, MappingNode)

    with raises(ValueError):
        fitter.fit_node(Foo, node)

    assert not node.fit_success
    assert node.missing_keys == []
    assert node.unwanted_keys == []


def test_mapping_node_dataclass_unwanted_field():
    fitter = Fitter(no_unwanted_keys=True)

    @dataclass
    class Foo:
        x: int
        y: int

    node = fitter._as_node({"x": 1, "y": 2, "z": 3})
    assert isinstance(node, MappingNode)

    with raises(ValueError):
        fitter.fit_node(Foo, node)

    assert not node.fit_success
    assert node.missing_keys == []
    assert node.unwanted_keys == ["z"]

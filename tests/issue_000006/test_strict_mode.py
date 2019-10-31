from typing import List, NamedTuple
from dataclasses import dataclass
from pytest import raises

from typefit import typefit, Config


def test_strict_mode_named_tuple():

    class Item(NamedTuple):
        id: int
        title: str
        versions: List[int]


    # Data as per the type
    data1 = {
        'id': 1,
        'title': 'Data 1',
        'versions': [1, 2, 3]
    }

    # Expected  output
    item_instance = Item(**data1)

    # Must return original data
    assert typefit(Item, data1) == item_instance

    # Data with extra key
    data2 = {
        'id': 1,
        'title': 'Data 1',
        'versions': [1, 2, 3],
        'new_key': 'new_data'
    }

    # With default config it must return data without extra key
    assert typefit(Item, data2) == item_instance

    # With strict config it must raise an error.
    with raises(ValueError):
        typefit(Item, data2, config=Config(strict_mapping=True))


def test_strict_mode_dataclass():

    @dataclass
    class Item:
        id: int
        title: str
        versions: List[int]


    # Data as per the type
    data1 = {
        'id': 1,
        'title': 'Data 1',
        'versions': [1, 2, 3]
    }

    # Expected  output
    item_instance = Item(**data1)

    # Must return original data
    assert typefit(Item, data1) == item_instance

    # Data with extra key
    data2 = {
        'id': 1,
        'title': 'Data 1',
        'versions': [1, 2, 3],
        'new_key': 'new_data'
    }

    # With default config it must return data without extra key
    assert typefit(Item, data2) == item_instance

    # With strict config it must raise an error.
    with raises(ValueError):
        typefit(Item, data2, config=Config(strict_mapping=True))

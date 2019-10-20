from typefit import typefit
from typing import Any, Text, Dict
from pytest import raises


def test_any():
    assert typefit(Any, 42) == 42
    assert typefit(Any, 'foo') == 'foo'


def test_dict():
    assert typefit(Dict, {'a': 1}) == {'a': 1}
    assert typefit(Dict[Text, int], {'a': 1}) == {'a': 1}

    with raises(ValueError):
        typefit(Dict[Text, int], {'a': '1'})

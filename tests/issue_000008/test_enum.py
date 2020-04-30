from enum import Enum

from pytest import raises

from typefit import typefit


def test_enum():
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = "blue"

    assert typefit(Color, 1) == Color.RED
    assert typefit(Color, 2) == Color.GREEN
    assert typefit(Color, "blue") == Color.BLUE

    with raises(ValueError):
        typefit(Color, 4)

    with raises(ValueError):
        typefit(Color, "string")

from dataclasses import dataclass
from typing import Mapping, Sequence

from typefit import typefit


@dataclass
class Something:
    seq: Sequence[int]
    map: Mapping[str, int]


def test_broader_types():
    x: Something = typefit(
        Something,
        dict(
            seq=[1, 2, 3],
            map=dict(a=1, b=2, c=3),
        ),
    )

    assert x.seq == [1, 2, 3]
    assert x.map == dict(a=1, b=2, c=3)

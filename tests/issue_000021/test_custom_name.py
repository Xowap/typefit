from dataclasses import dataclass, field
from typing import Text

from typefit import meta, other_field, typefit


@dataclass
class Info:
    some_thing: Text = field(metadata=meta(source=other_field("someThing")))


def test_custom_name():
    x: Info = typefit(Info, {"someThing": "foo"})
    assert x.some_thing == "foo"

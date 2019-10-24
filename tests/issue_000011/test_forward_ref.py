from dataclasses import dataclass, field
from typing import List, Text

from typefit import typefit


@dataclass
class Comment:
    text: Text
    children: List["Comment"] = field(default_factory=list)


data = {"text": "Hello", "children": [{"text": "Howdy"}, {"text": "Hello to you too"}]}


def test_forward_ref():
    comment = typefit(Comment, data)
    assert comment.children[0].text == "Howdy"

from typing import Any, Callable, Dict, Optional, Text

Mapping = Dict[Text, Any]


def meta(source: Optional[Callable[[Mapping], Any]] = None):
    """
    Generates the field metadata for

    Parameters
    ----------
    source
        Source function, that given the mapping as input will provide the
        value as output. If the value isn't found in the mapping, a KeyError
        should arise.
    """

    out = {}

    if source:
        out["typefit_source"] = source

    return out


def other_field(name: Text):
    """
    Looks for the value in a field named name.

    Parameters
    ----------
    name
        Name of the field to look for the value into.
    """

    def get(mapping: Dict[Text, Any]):
        return mapping[name]

    return get

from typing import Any, Callable, Dict, Mapping, NamedTuple, Optional, Text


class Source(NamedTuple):
    """
    Provides a way back and forth to convert the data from and to a JSON
    structure. Since the conversion from JSON is able to dig into any number
    of fields from the original mapping, the conversion to JSON will have to
    produce a dictionary as output, even if it has only one key.
    """

    value_from_json: Callable[[Mapping[str, Any]], Any]
    value_to_json: Callable[[Text, Any], Dict]


def meta(
    source: Optional[Source] = None,
    inject_root: bool = False,
    context: Optional[str] = None,
):
    """
    Generates the field metadata for a field based on what arguments are
    provided. By example, to source a field into a field with another name in
    the JSON data, you can do something like:

    >>> @dataclass
    >>> class Foo:
    >>>     x: int = field(metadata=meta(source=other_field('x')))

    See Also
    --------
    other_field

    Parameters
    ----------
    source
        Source function, that given the mapping as input will provide the
        value as output. If the value isn't found in the mapping, a KeyError
        should arise.
    inject_root
        Whether or not Typefit should inject the root object into the field.
        This is useful when you want to have a reference to the root object
        from a child object.
    context
        Instead of getting this value from the parsed object, Typefit will
        inject this key from the context into the field. This is useful when
        you want to inject a value from the context into the object.
    """

    out = {}

    if sum([inject_root, context is not None, source is not None]) > 1:
        raise ValueError("Only one of inject_root, context and source can be provided.")

    if source:
        out["typefit_source"] = source

    if inject_root:
        out["typefit_inject_root"] = True

    if context:
        out["typefit_from_context"] = context

    return out


def other_field(name: Text) -> Source:
    """
    Looks for the value in a field named name.

    Parameters
    ----------
    name
        Name of the field to look for the value into.
    """

    def from_json(mapping: Mapping) -> Any:
        return mapping[name]

    def to_json(field_name: Text, obj: Any) -> Dict:
        return {name: getattr(obj, field_name)}

    return Source(from_json, to_json)

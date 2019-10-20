from inspect import Parameter, signature
from string import Formatter
from typing import Any, Callable, Dict, Text
from urllib.parse import quote_plus


def get_single_param(func) -> Parameter:
    """
    Returns the single first parameter of callable. Raises a value error if
    there is more or less than 1 parameter and checks that the parameter has
    a proper type annotation.
    """

    sig = signature(func)

    if len(sig.parameters) != 1:
        raise ValueError

    param = list(sig.parameters.values())[0]

    if param.kind not in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}:
        raise ValueError

    if param.annotation is Parameter.empty:
        raise ValueError

    return param


def loose_call(func: Callable, kwargs: Dict[Text, Any]):
    """
    Calls a function using only kwargs and drops extra parameters that are not
    required if there is no kwargs argument to collect extra arguments.
    """

    sig = signature(func)

    has_kwargs = False

    for param in sig.parameters.values():
        if param.kind == Parameter.VAR_KEYWORD:
            has_kwargs = True

    if not has_kwargs:
        expect = set(sig.parameters.keys())
        present = set(kwargs.keys())

        return func(**{k: kwargs[k] for k in (expect & present)})
    else:
        return func(**kwargs)


def callable_value(value, kwargs):
    """
    Used for optional callable options in the API generator.
    """

    if callable(value):
        return loose_call(value, kwargs)
    return value


class UrlFormatter(Formatter):
    """
    Just like a regular formatter except that all formatted variables are
    escaped to be URL-safe. It allows to create easily paths like
    @get("items/{item_id}.json") without worrying about escaping the ID.
    """

    def format_field(self, value, format_spec):
        out = super().format_field(value, format_spec)
        out = quote_plus(f"{out}")
        return out

import re
from collections import abc
from inspect import Parameter, isclass, signature
from string import Formatter
from typing import Any, Callable, Dict, Generic, Iterator, Text, TypeVar
from urllib.parse import quote_plus

CLASS_RE = re.compile(r"<class '([^']+)'>")

T = TypeVar("T")


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


def is_named_tuple(value: Any) -> bool:
    if isclass(value):
        test = issubclass
    else:
        test = isinstance

    return test(value, tuple) and hasattr(value, "_fields")


class OrderedSet(Generic[T], abc.MutableSet):
    """
    Behaves exactly like a set() except that the objects will be kept in order
    of insertion.

    Notes
    -----
    Internally it relies on dictionaries keeping order. This means that this
    will only work for Python 3.7+ (and CPython 3.6+).
    """

    def __init__(self, initial_data: Iterator[T] = tuple()):
        self._set = {k: True for k in initial_data}

    def add(self, x: T) -> None:
        self._set[x] = True

    def discard(self, x: T) -> None:
        try:
            del self._set[x]
        except KeyError:
            pass

    def __contains__(self, x: object) -> bool:
        return x in self._set

    def __len__(self) -> int:
        return len(self._set)

    def __iter__(self) -> Iterator[T]:
        yield from self._set


def format_type_name(t: Any) -> Text:
    """
    Heuristics to make a type name look nice. It might change in the future.

    Parameters
    ----------
    t
        Type whose name you want to format
    """

    out = f"{t}"

    m = CLASS_RE.match(out)

    if m:
        out = f"'{m.group(1)}'"

    if out == "'NoneType'":
        out = "'None'"

    return out

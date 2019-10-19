from inspect import isclass
from typing import (
    Any,
    Callable,
    List,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .utils import get_single_param

T = TypeVar("T")


def _handle_union(t: Type[T], value: Any) -> T:
    """
    When the specified type is a Union, we typefit every type from the union
    individually.

    Let's also note that Optional[T] is equivalent to Union[T, None] and thus
    it's this handler that manages optional things.
    """

    if not (get_origin(t) is Union):
        raise ValueError

    for sub_t in get_args(t):
        try:
            return typefit(sub_t, value)
        except ValueError:
            continue

    raise ValueError


def _handle_list(t: Type[T], value: Any) -> T:
    """
    Handles a List type annotation. The value is expected to be a standard
    Python list, iterables and other sequences might not work.
    """

    if not (get_origin(t) is list):
        raise ValueError
    elif not isinstance(value, list):
        raise ValueError

    args = get_args(t)

    if not args:
        raise ValueError

    return [typefit(args[0], x) for x in value]


def _handle_type(t: Type[T], value: Any) -> T:
    """
    Handles cases where the type is some builtin type or some class.

    If it's a builtin then the value is expected to be exactly of that type
    (except for float that also accepts integers, because integers are floats
    in JSON).

    If it's a class it will look at the signature of the constructor. It must
    have exactly one argument which is annotated with a simple type. This
    allows to create "parsing" types, see the `typefit.narrows` module for
    examples.
    """

    if not isclass(t):
        raise ValueError

    if t is int:
        if not isinstance(value, int):
            raise ValueError
    elif t is float:
        if not isinstance(value, (int, float)):
            raise ValueError
    elif t is str:
        if not isinstance(value, str):
            raise ValueError
    elif t is bool:
        if not isinstance(value, bool):
            raise ValueError
    else:
        param = get_single_param(t)

        if not isclass(param.annotation) or not isinstance(value, param.annotation):
            raise ValueError

    return t(value)


def _handle_named_tuple(t: Type[T], value: Any) -> T:
    """
    This maps a dictionary into a type-annotated named tuple. All field
    declared in the tuple must be found in the dictionary and extra fields
    in the dictionary will be ignored.

    So far, default values in the named tuple are not taken in account so
    all fields are indeed required to be found in the dictionary (not just the
    ones you want to set).
    """

    if not isclass(t):
        raise ValueError

    if not issubclass(t, tuple):
        raise ValueError

    info = get_type_hints(t)

    if not info:
        raise ValueError

    if not isinstance(value, dict):
        raise ValueError

    kwargs = {}

    try:
        for key, sub_t in info.items():
            kwargs[key] = typefit(sub_t, value[key])
    except KeyError:
        raise ValueError

    return t(**kwargs)


def _handle_none(t: Type[T], value: Any) -> T:
    """
    If the type specification is either None or NoneType then we allow None
    values.
    """

    if t is not None and t is not None.__class__:
        raise ValueError

    if value is not None:
        raise ValueError

    return None


def _handle(handlers: List[Callable[[Type[T], Any], T]], t: Type[T], value: Any):
    """
    Given a list of handler functions, execute them in order and return the
    value of the first one that doesn't raise a ValueError. If no conversion
    can be found then a ValueError is raised.
    """

    for func in handlers:
        try:
            return func(t, value)
        except ValueError:
            continue

    raise ValueError


_handlers = [func for name, func in locals().items() if name.startswith("_handle_")]


def typefit(t: Type[T], value: Any) -> T:
    """
    Fits a JSON-decoded value into native Python type-annotated objects.
    Recognized types are:

    - Simple builtins (`int`, `float`, `bool`, `str`, `None`)
    - Lists
    - Mapping a dictionary into a `NamedTuple`
    - Custom types (eg dates, see the `typefit.narrows` module)
    """

    return _handle(_handlers, t, value)

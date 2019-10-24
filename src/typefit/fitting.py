from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Callable, List, Type, TypeVar, Union, get_type_hints

from .compat import get_args, get_origin
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


def _handle_mappings(t: Type[T], value: Any) -> T:
    """
    This maps a dictionary into a type-annotated named tuple or dataclass. All
    fields declared in the tuple/class must be found in the dictionary and
    extra fields in the dictionary will be ignored.

    So far, default values in the named tuple/class are not taken in account so
    all fields are indeed required to be found in the dictionary (not just the
    ones you want to set).
    """

    if not isclass(t):
        raise ValueError

    if not issubclass(t, tuple) and not is_dataclass(t):
        raise ValueError

    info = get_type_hints(t)

    if not info:
        raise ValueError

    if not isinstance(value, dict):
        raise ValueError

    kwargs = {}

    for key, sub_t in info.items():
        try:
            kwargs[key] = typefit(sub_t, value[key])
        except KeyError:
            pass

    try:
        return t(**kwargs)
    except TypeError:
        raise ValueError


def _handle_any(t: Type[T], value: Any) -> T:
    """
    If the type is Any then accept everything as-is
    """

    if t is not Any:
        raise ValueError

    return value


def _handle_dict(t: Type[T], value: Any) -> T:
    """
    Handles dictionaries. If the dictionary does not specify any types then
    nothing is coerced and the dict is returned as-is. However if the dict is
    defined with types (like Dict[Text, Text] by example) then the types are
    coerced.
    """

    if get_origin(t) is not dict:
        raise ValueError

    if not isinstance(value, dict):
        raise ValueError

    key_t, value_t = get_args(t)

    if isinstance(key_t, TypeVar) or isinstance(value_t, TypeVar):
        return value
    else:
        return {typefit(key_t, k): typefit(value_t, v) for k, v in value.items()}


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

    Parameters
    ----------
    t
        Type to fit the value into. Currently supported types are:

          - Simple builtins like :class:`int`, :class:`float`,
            :class:`typing.Text`, :class:`typing.bool`
          - Custom types. The constructor needs to accept exactly one parameter
            and that parameter should have a typing annotation.
          - :class:`typing.Union` to define several possible types
          - :class:`typing.List` to declare a list and the type of list values
    value
        Value to be fit into the type

    Returns
    -------
    T
        If the value fits, a value of the right type is returned.

    Raises
    ------
    ValueError
        When the fitting cannot be done, a :class:`ValueError` is raised.
    """

    return _handle(_handlers, t, value)

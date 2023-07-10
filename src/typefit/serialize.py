from collections import ChainMap, abc
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from json import dumps
from typing import Any, get_type_hints
from uuid import UUID

from .meta import Source


class Serializer:
    """
    Base serializer, that has no opinion and will serialize anything that is
    100% to serialize without making any assumption.

    Supported types are:

    - Numbers (int, float)
    - Booleans
    - Strings
    - Sequences
    - Mappings
    - Named (and typed) tuples
    - Dataclasses (including with Typefit metadata in the field)
    - Any object with a `__typefit_serialize__()` method
    - Enums

    You'll notice that the behavior of this class is a best effort to make
    something sane and simple. This means there is no warranty that this works:

    >>> base: SomeData = # Some data
    >>> serialized = serialize(base)
    >>> assert typefit(SomeData, serialized) == base

    If you want more types to be recognized by this serializer, you can inherit
    from it and extend the :py:meth:`~.Serializer.find_serializer()` method.

    If you don't know where to look, check out the following methods:

    - :py:meth:`~.typefit.serialize.Serializer.serialize`
    - :py:meth:`~.typefit.serialize.Serializer.json`

    See Also
    --------
    SaneSerializer
    """

    def find_serializer(self, obj: Any):
        """
        Trying to be as generic as possible. There is a few tricks there, like
        strings which are also sequences so the order of tests matters quite a
        lot.

        Please override this if you want to change the behavior. See how it's
        done in :py:class:`~.typefit.serialize.SaneSerializer` for an idea
        on how to do it.
        """

        if hasattr(obj, "__typefit_serialize__"):
            return self.serialize_typefit
        elif isinstance(obj, (int, float, bool, str)) or obj is None:
            return self.serialize_generic
        elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
            return self.serialize_tuple
        elif is_dataclass(obj):
            return self.serialize_dataclass
        elif isinstance(obj, abc.Sequence):
            return self.serialize_sequence
        elif isinstance(obj, abc.Mapping):
            return self.serialize_mapping
        elif isinstance(obj, Enum):
            return self.serialize_enum

    def serialize_generic(self, obj: Any) -> Any:
        """
        By default, leave the object untouched
        """

        return obj

    def serialize_tuple(self, obj: tuple):
        """
        Named tuples are expected to have typing annotations, we'll use that
        as a reference to get the fields list, however types are not enforced.
        """

        return {
            k: self.serialize(getattr(obj, k)) for k in get_type_hints(obj.__class__)
        }

    def serialize_sequence(self, obj: abc.Sequence):
        """
        Sequences are converted to regular lists, and each item of the list
        is recursively serialized.
        """

        return [self.serialize(x) for x in obj]

    def serialize_typefit(self, obj: Any):
        """
        Serializes an object by calling its `__typefit_serialize__()` method.
        """

        return obj.__typefit_serialize__()

    def serialize_dataclass(self, obj: Any):
        """
        Dataclasses are mappings but they merit a special attention due to the
        fact that their fields are not necessarily the fields that will be
        used in the output, thanks to the `meta(source=X)` feature.

        Notes
        -----
        See :py:class:`~.typefit.meta.Source`, but basically the conversion to
        JSON structure generates a series of dictionaries that are then
        superposed into a single dictionary and returned.

        All values of this dictionary are of course recursively serialized.
        """

        def _get_values():
            for field in fields(obj.__class__):
                source: Source

                match (field.metadata):
                    case {"typefit_source": source}:
                        yield {
                            k: self.serialize(v)
                            for k, v in source.value_to_json(field.name, obj).items()
                        }
                    case {"typefit_inject_root": True} | {"typefit_from_context": _}:
                        pass
                    case _:
                        yield {field.name: self.serialize(getattr(obj, field.name))}

        return dict(ChainMap(*_get_values()))

    def serialize_mapping(self, obj: abc.Mapping):
        """
        Mappings are just copied into another mapping. While copying, all the
        values are recursively serialized.
        """

        return {k: self.serialize(v) for k, v in obj.items()}

    def serialize_enum(self, obj: Enum):
        """
        Enums are serialized into their value.
        """

        return self.serialize(obj.value)

    def serialize(self, obj: Any):
        """
        Transforms a given object into a structure of basic types which can
        easily be serialized to JSON. It is not a strict inverse of
        :py:func:`~.typefit.typefit` but it should be good enough for most
        uses.

        Please note that this at least assumes that objects are consistent with
        their type declarations, no additional security is put in place.

        This method relies on the :py:meth:`~.Serializer.find_serializer()`
        method, which means that if you implement a subclass in order to
        change the mapping of serialization functions you should override
        :py:meth:`~.Serializer.find_serializer()`.

        Parameters
        ----------
        obj
            Object to be serialized
        """

        serializer = self.find_serializer(obj)
        return serializer(obj)

    def json(self, obj: Any) -> str:
        """
        Shortcut to transform an object into a JSON string going through
        :py:meth:`~.serialize`.
        """

        return dumps(self.serialize(obj))


class SaneSerializer(Serializer):
    """
    Opinionated version of what sane default for non-JSON-standard types
    should be. Comes as an extension of
    :py:class:`~.Serializer`.

    - Dates are serialized to the ISO format
    - UUIDs are serialized into their default str() representation
    """

    def find_serializer(self, obj: Any):
        """
        Tries to find special cases and if none of them are matched then
        resort to the parent method.
        """

        if isinstance(obj, datetime):
            return self.serialize_std_datetime
        elif isinstance(obj, date):
            return self.serialize_std_date
        elif isinstance(obj, UUID):
            return self.serialize_uuid
        else:
            return super().find_serializer(obj)

    def serialize_uuid(self, obj: UUID):
        """
        UUIDs are simply converted to strings
        """

        return f"{obj}"

    def serialize_std_datetime(self, obj: datetime):
        """
        Datetime are converted into ISO format
        """

        return obj.isoformat()

    def serialize_std_date(self, obj: date):
        """
        Dates are converted to ISO format
        """

        return obj.isoformat()


def serialize(obj: Any) -> Any:
    """
    Shortcut to use the :py:class:`~.typefit.serialize.SaneSerializer`'s
    :py:meth:`~.typefit.serialize.Serializer.serialize` method.

    Parameters
    ----------
    obj
        Object to be serializer
    """

    return SaneSerializer().serialize(obj)

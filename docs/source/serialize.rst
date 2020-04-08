Serializing objects
===================

Typefit also comes with the ability to serialize objects into a JSON-encodable
structure. While there is no strict warranty that
:py:func:`~.typefit.serialize.serialize` is the strict inverse function of
:py:func:`~.typefit.typefit` function, it is engineered so that the delta
should be minimal by default and that you have a way to get to the result
you want.

Usage
-----

The default behavior tries to be sane and straightforward. It is calibrated so
that if you can deserialize things using :py:func:`~.typefit.typefit` then they
should look the same when going back through
:py:func:`~.typefit.serialize.serialize`.

.. code-block:: python

    from typefit import serialize
    from typing import NamedTuple

    class Foo(NamedTuple):
        x: int
        y: int

    assert serialize(Foo(1, 2)) == {"x": 1, "y": 2}

Choosing your serializer
++++++++++++++++++++++++

Of course, it's not always so simple. That's why typefit lets you choose your
serializer and gives you the opportunity to customize it.

- :py:class:`~.typefit.serialize.Serializer` is the basic serializer that will
  only do 100% safe operations. However, it could be a bit limited for types
  who have no clear conversion between JSON and Python, typically like dates.
- :py:class:`~.typefit.serialize.SaneSerializer` adds some sane defaults to the
  mix to help you serialize dates and UUIDs without worrying too much.
- You can inherit from either of those if you want to create your own
  serializer. In that case you'll probably want to override the
  :py:class:`~.typefit.serialize.Serializer.find_serializer` method in your
  subclass to obtain the desired behavior.

The :py:func:`~.typefit.serialize.serialize` shortcut will use the
:py:class:`~.typefit.serialize.SaneSerializer` class.

Local behavior
++++++++++++++

If you want one specific object to serialize in a different way than what the
serializer has in mind, you can add a :code:`__typefit_serialize__()` method
to it and this method will be called in stead of the serializer's method.

By example:

.. code-block:: python

    from typing import NamedTuple
    from typefit import serialize

    class IntString(int):
        def __typefit_serialize__(self):
            return f"{self}"

    class Foo(NamedTuple):
        x: IntString

    foo = Foo(IntString(42))

    assert serialize(foo) == {"x": "42"}

Reference
---------

Narrows are data types that integrate some form of parsing to generate Python
objects from more generic types like strings. All those classes accept exactly
one argument to their constructor which is the data structure to convert.

.. automodule:: typefit.serialize
    :members:

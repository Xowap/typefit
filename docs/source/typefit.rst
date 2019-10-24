Fitting data into types
=======================

The base feature of typefit is to fit data into Python data structures. By
example:

.. code-block:: python

    from typing import NamedTuple, Text
    from typefit import typefit


    class Item(NamedTuple):
        id: int
        title: Text


    item = typefit(Item, {"id": 42, "title": "Item title yay"})
    assert item.title == "Item title yay"

It will use typing annotations in order to understand what kind of data
structure you expect and then it will create an instance of the specified type
based on the provided data.

Fitting mappings
----------------

The concept is as simple as that but it can become pretty powerful. Firstly,
typing definitions can be recursive, so this would work:

.. code-block:: python

    from dataclasses import dataclass, field
    from typing import List, Text
    from typefit import typefit


    @dataclass
    class Comment:
        text: Text
        children: List["Comment"] = field(default_factory=list)


    data = {
        "text": "Hello",
        "children": [
            {
                "text": "Howdy",
            },
            {
                "text": "Hello to you too",
            },
        ]
    }

    comment = typefit(Comment, data)

You'll notice that we switched from :class:`typing.NamedTuple` to a
`dataclass`. Both approaches work, that's up to you to decide which fits your
needs most.

.. note::

   This example uses a forward reference as type because the :class:`Comment`
   is not defined at the time we need it. This means that Python will have to
   be able to resolve this reference later, meaning that this class has to be
   importable. If hidden inside a 2-nd order function it won't work.

Parsing narrow types
--------------------

This system also allows you to parse input and coerce it into a more pythonic
object. A typical example for that would be to parse a date. Typefit uses
:code:`pendulum` in order to parse dates and will return a Pendulum date time
object.

.. code-block:: python

    from typefit import narrows, typefit

    data = "2019-01-01T00:00:00Z"
    date = typefit(narrows.DateTime, data)

    assert date.month == 1

Narrows are types that will help narrow-down

Reference
---------

You'll find here the reference of the public API. Private function are
documented in the source code but might change or disappear without notice.
The current API is not stable but will try to change as little as possible
before version 1.

Typefit
+++++++

The core typefit module only exposes one function.

.. autofunction:: typefit.typefit

Narrows
+++++++

Narrows are data types that integrate some form of parsing to generate Python
objects from more generic types like strings. All those classes accept exactly
one argument to their constructor which is the data structure to convert.

.. automodule:: typefit.narrows
    :members:

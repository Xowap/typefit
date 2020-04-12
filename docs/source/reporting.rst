Error Reporting
===============

Not every fit goes smoothly and especially when you're building your model you
will get misfits. If the system just told you blindly "there's an error" it
would not be very convenient, that's why ``typefit`` was built around the idea
of providing great error feedback.

.. note::

   This feature is still experimental because it needs to be in the wild for a
   while before making any definitive decisions.

Default behavior
----------------

By default, errors will be reported using the ``logging`` module and will
be output with True Colors ANSI codes.

This is the output of the default fitter:

.. code-block:: python

    Fitter(
        error_reporter=LogErrorReporter(
            formatter=PrettyJson5Formatter(colors='terminal16m')
        )
    )

This means that if you call :py:func:`~.typefit.typefit` directly and a parsing
error occurs, right before the ``ValueError`` exception is raised, the logger
will receive a message explaining the error.

Rationale
---------

The main goal of error reporting is that humans are able to understand the
error.

Errors might occur in simple structures but they are more likely to happen in
complicated recursive structures.

Suppose that you have a list of a thousand items and hidden in that list there
is just one or two items that don't match. Or the opposite, all items have an
error. Or even worse, you have a recursive structure with unions which generate
an exponentially high number of matching errors.

How do you display these errors without flooding the user's console?

The main idea behind the error reporting in ``typefit`` is that errors should
be displayed on top of the data, this way you can't have more error than fields
in your data.

On top of that, errors are abbreviated as much as possible. Objects that don't
contain errors are not expanded. Lists that have a thousand times the same
error will only display the error once. Strings that are too long will get
truncated.

Those constraints lead to develop the
:py:class:`~.typefit.reporting.PrettyJson5Formatter` formatter, which will
generate colored and annotated output, easy to grasp when looking for an error.

.. note::

   For now, everything is very oriented towards a developer that sees some
   output in a terminal to help them debug things. This explains the very
   opinionated nature of default configuration. Feel free to open tickets to
   make default more sane for other configurations!

Custom behavior
---------------

Maybe that you are not happy with the default behavior and you wish to change
it with custom reporting/formatting. This is possible through the fact that
you can configure what you want when creating the :py:class:`~.typefit.Fitter`
instance.

Reporter
++++++++

By creating an implementation of :py:class:`~.typefit.reporting.ErrorReporter`
that you then pass to the constructor of :py:class:`~.typefit.Fitter`, you can
then get notified of every error and report it.

The default reporter reports to the ``logging`` however feel free to report to
whichever tool you want, be it a live front-end or an IDE plugin.

If your reporter reports text, you might be interested in using the standard
formatter interface, as explained right below.

Formatter
+++++++++

While you don't have to use the formatter when doing a reporter, if the
reporter is going to report text then you can use this interface.

That formatter will take in the node that has an error and will output a
legible text that can be understood by the user.

Formatters must implement the :py:class:`~.typefit.reporting.ErrorFormatter`
interface.

The default formatter, :py:class:`~.typefit.reporting.PrettyJson5Formatter`,
is very opinionated and will generate shortened JSON5 outputs that are easy to
read and potentially colored using Pygments (AINSI codes, HTML, IRC, ...).

Reference
---------

For more information about the implementations, you can have a look at the
reference documentation.

Reporting
+++++++++

The ``reporting`` module has all the reporting logic.

.. automodule:: typefit.reporting
    :members:

Nodes
+++++

The full output of a parsing, including error messages, is held by the ``Node``
models. If you are making a custom formatter or reporter, you might have to
work with this API.

.. automodule:: typefit.nodes
    :members:

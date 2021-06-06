import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import ERROR, getLogger
from typing import Iterator, List, Text

from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers.javascript import JavascriptLexer

from .nodes import *

logger = getLogger("typefit")


class ErrorFormatter(ABC):
    """
    This interface is in charge of converting the meta information from
    :py:class:`~.typefit.nodes.Node` into some readable text report. That's
    useful for some reporters, like the :py:class:`~.LogErrorReporter`.
    """

    @abstractmethod
    def format(self, node: "Node") -> Text:
        """
        Implement this in order to transform the node into some readable text.

        Parameters
        ----------
        node
            Node that failed to be parsed, with errors
        """

        raise NotImplementedError


class ErrorReporter(ABC):
    """
    Implement this interface to be able to report errors. Once configured into
    the :py:class:`~.typefit.Fitter`, every time a fitting fails this will be
    triggered with the node that failed to be converted so that the error can
    be reported to the developer for debugging purposes.

    You can imagine reporters that send the error to the logging module
    (see :py:class:`~.LogErrorReporter`) but it could as well be displaying
    the data in an interactive web page or an IDE plugin to help seeing clearly
    what is happening.
    """

    @abstractmethod
    def report(self, node: "Node") -> None:
        """
        Will be called by :py:class:`~.typefit.Fitter` for every error.
        Override it in order to report the error wherever you want to report it
        to.

        Parameters
        ----------
        node
            Node that failed to fit
        """

        raise NotImplementedError


class LogErrorReporter(ErrorReporter):
    """
    Reports the errors into the logging module

    Parameters
    ----------
    formatter
        Formatter to use
    level
        Log level to report the errors with
    """

    def __init__(self, formatter: ErrorFormatter, level: int = ERROR):
        self.formatter = formatter
        self.level = level

    def report(self, node: "Node") -> None:

        logger.log(self.level, "Fitting error:\n\n%s", self.formatter.format(node))


@dataclass
class _Line:
    """
    Internal utility class to represent a line that might have errors above
    its head.

    - ``level`` -- Indent level
    - ``content`` -- Content of the line
    - ``errors`` -- List of errors attributed to that line
    """

    level: int
    content: Text
    errors: List[Text] = field(default_factory=list)


class PrettyJson5Formatter(ErrorFormatter):
    """
    Formats the data into annotated and redacted JSON5. The goal here is to
    display the errors on top of the actual data, while removing all the data
    that is not useful to understand the error itself.

    The output can be colored by Pygments, just fill in the ``colors`` argument
    with a valid Pygments formatter name (could be ANSI codes, could be HTML,
    could be whatever you desire).

    Parameters
    ----------
    indent
        Content of one ident level (default = 4 spaces)
    colors
        Pygments color formatter. No coloring happens if this string is
        empty.
    truncate_strings_at
        If a string is longer than this indicated length then it will be
        truncated for display. Default is 40, put 0 to disable the feature.
    """

    def __init__(
        self,
        indent: Text = "    ",
        colors: Text = "",
        truncate_strings_at: int = 40,
    ):
        self.indent = indent
        self.colors = colors
        self.truncate_strings_at = truncate_strings_at
        self._previous_level = -1

    def _indent(self, level: int) -> Text:
        """
        Generates the indent for the given indent level
        """

        return self.indent * level

    def _line(self, line: _Line) -> Text:
        """
        Generates the output for a given line.

        Notes
        -----
        There is some fancy logic here to make sure that if there is errors
        on the line and if it's not the first line at this indent level then
        we should leave a blank line above. This is to make it clear which line
        the error comments are attached to.

        Parameters
        ----------
        line
            Line to print
        """

        out = "\n".join(
            [
                *([""] if line.errors and line.level == self._previous_level else []),
                *(f"{self._indent(line.level)}// {e}" for e in line.errors),
                f"{self._indent(line.level)}{line.content}",
            ]
        )

        self._previous_level = line.level

        return out

    def _format_flat(
        self, node: FlatNode, level: int, prefix: Text, suffix: Text
    ) -> Iterator[_Line]:
        """
        Formats a flat literal using the standard JSON function.

        Notes
        -----
        String-truncating logic happens here, that's why this function is a
        little bit more complicated.
        """

        if (
            isinstance(node.value, str)
            and self.truncate_strings_at
            and len(node.value) > self.truncate_strings_at
        ):
            value = f"{node.value[:self.truncate_strings_at]}[...]"
            extra = " /* truncated */"
        else:
            value = node.value
            extra = ""

        out = _Line(
            level, f"{prefix}{json.dumps(value, ensure_ascii=False)}{extra}{suffix}"
        )

        if not node.fit_success:
            out.errors.extend(node.errors)

        yield out

    def _format_list(
        self, node: ListNode, level: int, prefix: Text, suffix: Text
    ) -> Iterator[_Line]:
        """
        Formats a list. Same logic as :py:meth:`~._format_mapping` except for
        lists.
        """

        if not node.problem_is_kids:
            if node.value:
                content = " /* ... */ "
            else:
                content = ""

            yield _Line(level, f"{prefix}[{content}]{suffix}", [*node.errors])
        else:
            yield _Line(level, f"{prefix}[", [*node.errors])

            errors = set()
            to_display = []

            for child in node.children:
                child_errors = tuple(child.errors)

                if not child.fit_success and child_errors not in errors:
                    errors.add(child_errors)
                    to_display.append(child)

            for child in to_display:
                yield from self._format(child, level + 1, "", ",")

            yield _Line(level, f"]{suffix}")

    def _format_mapping(
        self, node: MappingNode, level: int, prefix: Text, suffix: Text
    ) -> Iterator[_Line]:
        """
        Formats a mapping.

        - If the problem is not in the kids (maybe an int was expected and an
          object was received, by example) then just abreviate the object and
          put the error on top
        - If the problem is with the kids, recursively renders the kids to
          help the developer figuring out which kid is misbehaving
        """

        if not node.problem_is_kids:
            if node.value:
                content = " /* ... */ "
            else:
                content = ""

            yield _Line(level, f"{prefix}{{{content}}}{suffix}", [*node.errors])
        else:
            yield _Line(level, f"{prefix}{{", [*node.errors])

            for key, child in node.children.items():
                yield from self._format(child, level + 1, f"{json.dumps(key)}: ", ",")

            if node.missing_keys:
                yield _Line(
                    level + 1,
                    f'// Missing keys: {", ".join(repr(k) for k in node.missing_keys)}',
                )

            yield _Line(level, f"}}{suffix}")

    def _format(
        self, node: Node, level: int = 0, prefix: Text = "", suffix: Text = ""
    ) -> Iterator[_Line]:
        """
        Will recursively generate the format of a line. Depending on the node
        type, the right formatter will be chosen and all the generated lines
        will be iterated.

        Notes
        -----
        Here there is a prefix/suffix logic here which allows to easily put
        a coma after the line or a key name in front of the line without
        knowing beforehand where the line is going to be displayed or if it's
        the first/last line.

        Parameters
        ----------
        node
            Node to format
        level
            Indent level
        prefix
            Prefix to put before the line (on the first line)
        suffix
            Suffix to put after the line (on the last line)

        See Also
        --------
        _format_flat
        _format_list
        _format_mapping
        """

        # noinspection PyTypeChecker
        yield from {
            FlatNode: self._format_flat,
            ListNode: self._format_list,
            MappingNode: self._format_mapping,
        }[node.__class__](node, level, prefix, suffix)

    def format(self, node: "Node") -> Text:
        """
        Formats the node into JSON5. If colors were specified in the
        constructor, then it's also where the coloration is added before being
        returned.
        """

        out = "\n".join(map(self._line, self._format(node)))
        formatter = None

        if self.colors:
            formatter = get_formatter_by_name(self.colors)

        if formatter:
            out = highlight(out, JavascriptLexer(), formatter)

        return out

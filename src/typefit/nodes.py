from dataclasses import dataclass, field, fields, is_dataclass
from inspect import Parameter, Signature, isclass, signature
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Text,
    Tuple,
    Type,
    TypeVar,
    get_type_hints,
)

from .compat import get_args, get_origin
from .utils import OrderedSet, format_type_name, is_named_tuple

if TYPE_CHECKING:
    from .fitting import Fitter


__all__ = ["T", "Node", "MappingNode", "ListNode", "FlatNode", "LiteralNode"]


T = TypeVar("T")


def set_root_attr(obj: Any, attr: str):
    """
    2nd-order function to set the root object into `obj`'s attribute `attr`.
    See :py:meth:`typefit.fitting.Fitter.fit` for more information.

    See Also
    --------
    typefit.fitting.Fitter.fit
    """

    def do_it(value: Any):
        object.__setattr__(obj, attr, value)

    return do_it


@dataclass
class Node:
    """
    Typefit is made to convert JSON structure into Python dataclasses and
    objects. In order to make analyzing a fitting possible after it failed,
    data structures will be converted into a tree of Nodes. This is the base
    class, but there is 3 kinds of nodes:

    - :py:class:`~.FlatNode` -- "Flat" structures, aka numbers, strings, bools
      or nulls
    - :py:class:`~.MappingNode` -- For mappings (dictionaries, dataclasses and
      named tuples)
    - :py:class:`~.ListNode` -- For lists

    Each node will remember the errors that the decoder went through and if
    the decoding was successful at all. In other terms, by navigating through
    the nodes you can generate readable error reporting.

    Other Parameters
    ----------------
    fitter
        Fitter instance to refer to for configuration and fitting other nodes
    value
        Value of this node
    errors
        All unique errors encountered on this node. There might still be errors
        if the fitting was successful, as those errors record all attempts.
    fit_success
        Indicates if the fitting was successful at least once. This does not
        mean that the overall fitting went well and especially with unions this
        could be tricky.

    See Also
    --------
    FlatNode
    MappingNode
    ListNode
    """

    fitter: "Fitter" = field(repr=False)
    value: Any
    errors: Set[Text] = field(init=False, default_factory=OrderedSet, repr=False)
    fit_success: bool = field(init=False, default=False)

    def fit(self, t: Type[T]) -> T:
        """
        That is left to the subclasses to implement
        """

        raise NotImplementedError

    def fail(self, reason: Text) -> None:
        """
        Utility to trigger a failure

        - Register the error locally.
        - Raise a value error. Nodes that have children nodes need to catch the
          value errors from their children in order to not stop their own
          processing.

        Parameters
        ----------
        reason
            Reason to be given and registered as error
        """

        self.errors.add(reason)
        raise ValueError(reason)


@dataclass
class MappingNode(Node):
    """
    Those nodes are triggered by JSON "objects". They can map into different
    kinds of Python objects:

    - Plain old dictionaries (with string keys)
    - Dataclasses
    - Type-annotated named tuples

    Other Parameters
    ----------------
    children
        Dictionary of child nodes
    missing_keys
        After fitting, which keys were missing (warning, so far this is tricky
        for unions)
    unwanted_keys
        After fitting, which keys were unwanted (warning, so far this is tricky
        for unions)
    problem_is_kids
        Does the rejection come from the kids? Or is it due to this node only?
    """

    children: Dict[Text, Node] = field(repr=False)
    missing_keys: List[Text] = field(default_factory=list, repr=False)
    unwanted_keys: List[Text] = field(default_factory=list, repr=False)
    problem_is_kids: bool = field(default=False, repr=False)
    context: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def fit_dict(self, t: Type[T]) -> T:
        """
        Fitting a JSON object into a Python dictionary. That's basically just
        a copy with a few sanity checks (and typefitting on the values).

        Notes
        -----
        If we're fitting to a dictionary we're first going to make sure that
        the type spec makes sense and in particular that the keys are strings.
        Indeed, having keys being something else than strings would be much
        more complicated due to the mappings and other transformations
        happening. On the other side, we're doing this for JSON and there is
        no other possibility for keys.

        On the other hand, the values can be fitted into any type that the
        developer asks and a lot of the code is just doing this fitting and
        reporting errors.

        Parameters
        ----------
        t
            Should be a dictionary specification, otherwise it's going to fail
        """

        args = get_args(t)

        try:
            key_t, value_t = args
        except ValueError:
            key_t, value_t = Text, Any

        if isinstance(key_t, TypeVar):
            key_t = Text

        if not issubclass(key_t, str):
            self.fail("Dictionaries with non-string keys are not supported")

        if isinstance(value_t, TypeVar):
            value_t = Any

        failed = [False]

        def make_dict():
            for k, v in self.children.items():
                try:
                    if not isinstance(k, str):
                        v.fail(f"Key {k!r} is not a string")

                    yield k, self.fitter.fit_node(value_t, v)
                except ValueError:
                    failed[0] = True

        out = dict(make_dict())

        if failed[0]:
            self.problem_is_kids = True
            self.fail("Not all items are fit")

        self.fit_success = True
        return out

    def value_from_context(self, key: str) -> Callable[[], Any]:
        """
        Encapsulates the logic that we're gonna give to the LiteralNode
        when doing context injection
        """

        def get_value() -> Any:
            try:
                return self.context[key]
            except KeyError as e:
                raise ValueError(f"Key {key!r} is missing from the context") from e

        return get_value

    def fit_object(self, t: Type[T]) -> T:
        """
        Fitting into dataclasses and named tuples. On paper that's fairly
        simple, but if you want something safe with good error reporting it's
        a little bit more complicated.

        Notes
        -----
        The first thing that happens is different kinds of inspection on the
        type to figure what are the members of that object, what are their
        types, which ones are mandatory and which ones have a default value,
        etc.

        Then we'll look at each key into the source data and if the data is
        there it'll be fitted into the expected type.

        Please note that there is also some source mapping happening, if the
        dataclass metadata contains a source we're going to use the source
        function instead of directly digging into the value.

        Subsequently, with a few set operations, you can deduce which fields
        are missing, which fields are too much, etc. If anything is wrong, we
        report and fail.

        Finally, the object is instantiated. If the dataclass/named tuple has
        not been tampered with too much, this should pass since we've checked
        that the parameters are right. If there is some funny business going on
        then we're not going to be able to get a decent explanation to the
        user, even potentially crash the whole thing with no explanation. I
        have no better idea on how to handle this though.

        Parameters
        ----------
        t
            Type-annotated named tuple class or dataclass
        """

        sig = signature(t)
        hints = get_type_hints(t)

        fields_injections, fields_sources, root_fields = self.parse_dataclass(t)

        (
            expected,
            failed_keys,
            kwargs,
            literal_nodes,
            required,
        ) = self.make_constructor_kwargs(fields_injections, fields_sources, hints, sig)

        missing = required - set(kwargs) - set(failed_keys)
        unwanted = set(self.children) - expected
        errors = []

        self.report_missing(errors, missing)
        self.report_unwanted(errors, t, unwanted)
        self.report_failed(errors, failed_keys, fields_injections, literal_nodes)

        if errors:
            self.problem_is_kids = True
            self.fail(". ".join([f"Wrong keys set for {format_type_name(t)}", *errors]))

        return self.make_out_instance(kwargs, root_fields, t)

    def parse_dataclass(
        self, t: Type[T]
    ) -> Tuple[
        Mapping[str, Any],
        Mapping[str, Callable[[Mapping[str, Any]], Any]],
        Sequence[str],
    ]:
        """
        If the expected type is a dataclass, there might be some metadata on
        the fields. Which helps for example to source a field from a different
        field name or to inject context into given fields. We're extracting
        all this metadata from here (if relevant).

        Parameters
        ----------
        t
            The type of the object that we're instantiating
        """

        root_fields = []
        fields_sources = {}
        fields_injections = {}

        if not is_dataclass(t):
            return fields_injections, fields_sources, root_fields

        for t_field in fields(t):
            match (t_field.metadata):
                case {"typefit_source": source}:
                    fields_sources[t_field.name] = source.value_from_json
                case {"typefit_from_context": key}:
                    fields_injections[t_field.name] = self.value_from_context(key)
                case {"typefit_inject_root": True}:
                    fields_injections[t_field.name] = None
                    root_fields.append(t_field.name)

        return fields_injections, fields_sources, root_fields

    def make_constructor_kwargs(
        self,
        fields_injections: Mapping[str, Any],
        fields_sources: Mapping[str, Callable[[Mapping[str, Any]], Any]],
        hints: Any,
        sig: Signature,
    ) -> Tuple[
        Set[str],
        Sequence[str],
        Mapping[str, Any],
        Mapping[str, "LiteralNode"],
        Set[str],
    ]:
        """
        We're going through every field of the constructor's signature and we
        try to fit the corresponding value from the input JSON.

        We only support parameters that can be called by keyword, as this is
        what we're getting from a mapping type.

        For each field we got three possibilities:

        - The field has some meta mapping (most likely to get its value from
          another field) in which case we call the mapping function
        - Or it is subject to some kind of injection (either root or context),
          which requires to wrap the mapped value into a LiteralNode and to
          continue the resolution like that
        - Or finally it's a normal node and we just get its value

        Parameters
        ----------
        fields_injections
            The mapping of keys to the injection functions
        fields_sources
            The mapping of keys to the mapping functions
        hints
            The type hints of the constructor
        sig
            The signature of the constructor
        """

        literal_nodes: Dict[str, LiteralNode] = {}
        kwargs = {}
        required = set()
        expected = set()
        failed_keys = []

        param: Parameter
        for param in sig.parameters.values():
            if param.kind not in {
                Parameter.KEYWORD_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            }:
                continue

            expected.add(param.name)

            if param.default is param.empty:
                required.add(param.name)

            try:
                if param.name in fields_sources:
                    sub_v = fields_sources[param.name](self.children)
                elif param.name in fields_injections:
                    sub_v = LiteralNode(self.fitter, fields_injections[param.name])
                    literal_nodes[param.name] = sub_v
                else:
                    sub_v = self.children[param.name]

                if param.name not in hints:
                    sub_v.fail("Missing typing annotations")
            except KeyError:
                pass
            else:
                try:
                    kwargs[param.name] = self.fitter.fit_node(hints[param.name], sub_v)
                except ValueError:
                    failed_keys.append(param.name)

        return expected, failed_keys, kwargs, literal_nodes, required

    def report_missing(
        self, errors: MutableSequence[str], missing: Iterable[str]
    ) -> None:
        """
        Some keys might be missing from the input JSON. This is where we do
        the check and report them.

        Parameters
        ----------
        errors
            Output errors list
        missing
            The list of missing keys
        """

        if missing:
            self.missing_keys = [*missing]
            errors.append(f'Missing keys: {", ".join(repr(x) for x in missing)}')

    def report_unwanted(
        self, errors: MutableSequence[str], t: Type[T], unwanted: Iterable[str]
    ) -> None:
        """
        There is an option to report unwanted keys as errors. This is where
        we do the check.

        Parameters
        ----------
        errors
            Output errors list
        t
            The type of the object that we're instantiating
        unwanted
            The list of unwanted keys
        """

        if self.fitter.no_unwanted_keys and unwanted:
            self.unwanted_keys = [*unwanted]
            errors.append(f'Unwanted keys: {", ".join(repr(x) for x in unwanted)}')

            for k in unwanted:
                self.children[k].errors.add(f"Unwanted by {format_type_name(t)}")

    def report_failed(
        self,
        errors: MutableSequence[str],
        failed_keys: Sequence[str],
        fields_injections: Mapping[str, Any],
        literal_nodes: Mapping[str, "LiteralNode"],
    ) -> None:
        """
        If any sub-key failed to fit, we're going to report the error. One
        of two thing might have happened:

        - A "normal" key failed, aka it was impossible to fit the JSON value
          into the expected type.
        - An injection failed (in theory either root or context injection but
          in practice it's only context injection that can fail). In that case
          we'll report the error at this level as the goal is to be able to
          display the error on the input JSON and since it's an injection the
          value is not in the input JSON. Thus, the error will have to be
          displayed at the level of the parent node (aka this node).

        Parameters
        ----------
        errors
            Some output list which will contain errors
        failed_keys
            The list of keys that failed to fit
        fields_injections
            The mapping of keys to the injection functions
        literal_nodes
            The mapping of keys to the literal nodes
        """

        if failed_keys:
            if normal_failed_keys := set(failed_keys) - fields_injections.keys():
                errors.append(
                    f'No fit for keys: {", ".join(repr(x) for x in normal_failed_keys)}'
                )

            for key in failed_keys:
                if key in literal_nodes:
                    for error in literal_nodes[key].errors:
                        errors.append(error)

    def make_out_instance(
        self, kwargs: Mapping[str, Any], root_fields: Sequence[str], t: Type[T]
    ) -> T:
        """
        Generates the output instance from the kwargs.

        Additionally this function has the mission to report into which fields
        the root should be injected (if any). We know this from the root_fields
        parameter which comes from the dataclass parsing logic in
        :py:meth:`~.parse_dataclass`.

        Parameters
        ----------
        kwargs
            The kwargs that are going to be passed to the constructor
        root_fields
            The fields into which the root should be injected
        t
            The type of the object that we're instantiating
        """

        out = t(**kwargs)
        self.fit_success = True

        for field_name in root_fields:
            self.fitter.root_injectors.append(set_root_attr(out, field_name))

        return out

    def fit(self, t: Type[T]) -> T:
        """
        This detects if we're dealing with a fit into a dictionary or a fit
        into a named tuple/dataclass.

        Parameters
        ----------
        t
            Type to fit into, either a Dict either NamedTuple either a
            @dataclass
        """

        origin = get_origin(t)

        if origin is dict or (isclass(origin) and issubclass(origin, Mapping)):
            return self.fit_dict(t)
        elif is_named_tuple(t) or is_dataclass(t):
            return self.fit_object(t)
        else:
            self.fail(f"{format_type_name(t)} is not a mapping type")


@dataclass
class ListNode(Node):
    """
    Node that is parent to a list of other nodes. That's basically the
    application of the same type on a list of items instead of just one.

    Other Parameters
    ----------------
    children
        List of child nodes
    problem_is_kids
        Does the rejection come from the kids? Or is it due to this node only?
    """

    children: List[Node] = field(repr=False)
    problem_is_kids: bool = field(default=False, repr=False)

    def fit(self, t: Type[T]) -> T:
        """
        After some sanity checks, goes through the whole list to make sure
        that all the content fits. If some of them don't fit, still continue
        to try fitting the rest, for error reporting purposes.
        """

        origin = get_origin(t)
        is_list = origin is list
        is_seq = isclass(origin) and issubclass(origin, Sequence)

        if not (is_list or is_seq):
            self.fail(f"{format_type_name(t)} is not a list")

        args = get_args(t)

        if not args:
            self.fail("Could not determine list item type")

        failed = False
        out = []

        for child in self.children:
            try:
                out.append(self.fitter.fit_node(args[0], child))
            except ValueError:
                failed = True

        if failed:
            self.problem_is_kids = True
            self.fail("Not all list items fit")

        self.fit_success = True
        return out


@dataclass
class FlatNode(Node):
    """
    Flat nodes are mostly the builtin types (int, float, str, bool, None) but
    also can be class constructors if the constructor can accept what is being
    passed to it as an argument.
    """

    def fit_builtin(self, t: Type[T]) -> Optional[T]:
        """
        For builtins, we dumbly test one by one. Please note that there is a
        trick where an int can implicitly be converted into a float (since
        it's coming from JSON we know that the int precision is already the one
        of a float so we don't risk on loosing precision).

        Returns None when trying to convert into a type that is not a builtin.

        Parameters
        ----------
        t
            Type to convert into, if not a builtin the None will be returned
        """

        if t is int:
            if not isinstance(self.value, int):
                self.fail("Not an int")
            return self.value
        elif t is float:
            if not isinstance(self.value, (int, float)):
                self.fail("Neither a float nor an int")
            return float(self.value)
        elif t is str:
            if not isinstance(self.value, str):
                self.fail("Not a string")
            return self.value
        elif t is bool:
            if not isinstance(self.value, bool):
                self.fail("Not a bool")
            return self.value

    def fit_class(self, t: Type[T]) -> T:
        """
        Fitting the content into a class. That one is a bit tricky but
        basically if the constructor can accept one argument and that this
        argument is properly annotated and that the value can fit into that
        argument's type then the constructor will be called with the fitted
        argument.

        However, so far it only works with builtin types. Arbitrary types might
        come in later, but this is mostly here so that you can transform
        strings into dates.
        """

        if is_dataclass(t) or is_named_tuple(t):
            self.fail(f"{format_type_name(t)} can only fit an object")

        if t is list:
            self.fail(f"{format_type_name(t)} can only fit a list")

        try:
            sig = signature(t).bind(self.value)
        except TypeError:
            self.fail(
                "Constructor should be callable with exactly 1 positional argument"
            )

        (param_name,) = sig.arguments
        param: Parameter = sig.signature.parameters[param_name]

        if param.annotation is param.empty:
            self.fail("Constructor does not specify argument type")

        try:
            arg = self.fitter.fit(param.annotation, self.value)
        except ValueError:
            self.fail(
                f"Constructor {format_type_name(t)} expects "
                f"{param.annotation} but value does not fit"
            )

        return t(arg)

    def fit(self, t: Type[T]) -> T:
        """
        Tries to use the builtins to fit and if not tries to see if there is
        a constructor we can use.

        Parameters
        ----------
        t
            Type you're fitting into
        """

        if not isclass(t):
            self.fail(f"{t} is not a class")

        out = self.fit_builtin(t)

        if out is None:
            out = self.fit_class(t)

        self.fit_success = True
        return out


@dataclass
class LiteralNode(Node):
    """
    This kind of node is used to inject a literal value that we don't want to
    fit into anything. That's not really used on things coming from JSON, but
    rather wraps stuff like context injections.

    If the value is callable, it will be called without arguments. The callable
    is expected to raise ValueError if its internal validation fails.
    """

    def fit(self, t: Type[T]) -> T:
        if callable(self.value):
            try:
                return self.value()
            except ValueError as e:
                self.fail(e.args[0])
        else:
            return self.value

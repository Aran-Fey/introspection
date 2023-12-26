import ast
import builtins
import collections.abc
import inspect
import itertools
import os
import sys
import types
import typing
from numbers import Number
from typing import *  # type: ignore
from typing_extensions import Self

from renumerate import renumerate

from .bound_arguments import BoundArguments
from .parameter import Parameter
from .misc import unwrap, static_mro, static_vars
from ._utils import SIG_EMPTY
from .errors import *
from .types import P, TypeAnnotation

__all__ = ["Signature"]


T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
K = TypeVar("K")
V = TypeVar("V")
IntOrFloatVar = TypeVar("IntOrFloatVar", int, float)
FilePath = Union[str, bytes, os.PathLike[AnyStr]]

_BUILTIN_SIGNATURES: Dict[str, Tuple[TypeAnnotation, List[Parameter]]] = {
    "abs": (Any, [Parameter("x", Parameter.POSITIONAL_ONLY, annotation=SupportsAbs)]),
    "aiter": (
        AsyncIterator[T],  # type: ignore
        [
            Parameter(
                "async_iterable",
                Parameter.POSITIONAL_ONLY,
                annotation=AsyncIterable[T],  # type: ignore
            )
        ],
    ),
    "all": (
        bool,
        [Parameter("iterable", Parameter.POSITIONAL_ONLY, annotation=Iterable)],
    ),
    "anext": (
        Awaitable[Union[A, B]],  # type: ignore
        [
            Parameter(
                "async_iterator",
                Parameter.POSITIONAL_ONLY,
                annotation=AsyncIterator[A],  # type: ignore
            ),
            Parameter(
                "default",
                Parameter.POSITIONAL_ONLY,
                default=Parameter.missing,
                annotation=B,
            ),
        ],
    ),
    "any": (
        bool,
        [Parameter("iterable", Parameter.POSITIONAL_ONLY, annotation=Iterable)],
    ),
    "ascii": (str, [Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any)]),
    "bin": (str, [Parameter("x", Parameter.POSITIONAL_ONLY, annotation=int)]),
    "bool": (bool, [Parameter("x", Parameter.POSITIONAL_ONLY, Parameter.missing, Any)]),
    "breakpoint": (
        None,
        [
            Parameter("args", Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter("kwargs", Parameter.VAR_KEYWORD, annotation=Any),
        ],
    ),
    "bytearray": (
        bytearray,
        [
            Parameter(
                "source",
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.missing,
                Union[str, ByteString],
            ),
            Parameter("encoding", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
            Parameter("errors", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        ],
    ),
    "bytes": (
        bytes,
        [
            Parameter(
                "source",
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.missing,
                Union[str, ByteString, SupportsBytes],
            ),
            Parameter("encoding", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
            Parameter("errors", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        ],
    ),
    "callable": (
        bool,
        [Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any)],
    ),
    "chr": (str, [Parameter("i", Parameter.POSITIONAL_ONLY, annotation=int)]),
    "classmethod": (
        classmethod,
        [Parameter("method", Parameter.POSITIONAL_ONLY, annotation=Callable)],
    ),
    "compile": (
        types.CodeType,
        [
            Parameter(
                "source",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Union[str, ByteString, ast.AST],
            ),
            Parameter("filename", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
            Parameter(
                "mode",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Literal["eval", "exec"] if hasattr(typing, "Literal") else str,
            ),
            Parameter("flags", Parameter.POSITIONAL_OR_KEYWORD, 0, int),
            Parameter("dont_inherit", Parameter.POSITIONAL_OR_KEYWORD, False, bool),
            Parameter("optimize", Parameter.POSITIONAL_OR_KEYWORD, -1, int),
        ],
    ),
    "complex": (
        complex,
        [
            Parameter(
                "real",
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.missing,
                Union[int, float],
            ),
            Parameter(
                "imag",
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.missing,
                Union[int, float],
            ),
        ],
    ),
    "delattr": (
        None,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("name", Parameter.POSITIONAL_ONLY, annotation=str),
        ],
    ),
    "dict": (
        Dict[K, V],  # type: ignore
        [
            Parameter(
                "mapping_or_iterable",
                Parameter.POSITIONAL_ONLY,
                Parameter.missing,
                Union[Mapping[K, V], Iterable[Tuple[K, V]]],  # type: ignore
            ),
            Parameter("kwargs", Parameter.VAR_KEYWORD, annotation=V),
        ],
    ),
    "dir": (
        List[str],
        [Parameter("object", Parameter.POSITIONAL_ONLY, Parameter.missing, Any)],
    ),
    "divmod": (
        Tuple[IntOrFloatVar, IntOrFloatVar],  # type: ignore
        [
            Parameter("a", Parameter.POSITIONAL_ONLY, annotation=IntOrFloatVar),
            Parameter("b", Parameter.POSITIONAL_ONLY, annotation=IntOrFloatVar),
        ],
    ),
    "enumerate": (
        Iterator[Tuple[int, T]],  # type: ignore
        [
            Parameter(
                "iterable",
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Iterable[T],  # type: ignore
            ),
            Parameter("start", Parameter.POSITIONAL_OR_KEYWORD, 0, int),
        ],
    ),
    "eval": (
        Any,
        [
            Parameter(
                "expression",
                Parameter.POSITIONAL_ONLY,
                annotation=Union[str, types.CodeType],
            ),
            Parameter("globals", Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
            Parameter("locals", Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
        ],
    ),
    "exec": (
        None,
        [
            Parameter(
                "object",
                Parameter.POSITIONAL_ONLY,
                annotation=Union[str, types.CodeType],
            ),
            Parameter("globals", Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
            Parameter("locals", Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
        ],
    ),
    "filter": (
        Iterator[T],  # type: ignore
        [
            Parameter(
                "function",
                Parameter.POSITIONAL_ONLY,
                annotation=Callable[[T], Any],  # type: ignore
            ),
            Parameter(
                "iterable",
                Parameter.POSITIONAL_ONLY,
                annotation=Iterable[T],  # type: ignore
            ),
        ],
    ),
    "float": (
        float,
        [Parameter("x", Parameter.POSITIONAL_ONLY, Parameter.missing, SupportsFloat)],
    ),
    "format": (
        str,
        [
            Parameter("value", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("format_spec", Parameter.POSITIONAL_ONLY, Parameter.missing, str),
        ],
    ),
    "frozenset": (
        FrozenSet[T],  # type: ignore
        [
            Parameter(
                "iterable",
                Parameter.POSITIONAL_ONLY,
                Parameter.missing,
                Iterable[T],  # type: ignore
            )
        ],
    ),
    "getattr": (
        Any,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("name", Parameter.POSITIONAL_ONLY, annotation=str),
            Parameter("default", Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
        ],
    ),
    "globals": (dict, []),
    "hasattr": (
        bool,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("name", Parameter.POSITIONAL_ONLY, annotation=str),
        ],
    ),
    "hash": (
        int,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
        ],
    ),
    "help": (
        None,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
        ],
    ),
    "hex": (str, [Parameter("x", Parameter.POSITIONAL_ONLY, annotation=int)]),
    "id": (int, [Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any)]),
    "input": (
        str,
        [Parameter("prompt", Parameter.POSITIONAL_ONLY, Parameter.missing, Any)],
    ),
    "int": (
        int,
        [
            Parameter(
                "x",
                Parameter.POSITIONAL_ONLY,
                Parameter.missing,
                Union[str, ByteString, SupportsInt],
            ),
            Parameter("base", Parameter.POSITIONAL_ONLY, 10, int),
        ],
    ),
    "isinstance": (
        bool,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter(
                "classinfo",
                Parameter.POSITIONAL_ONLY,
                annotation=Union[type, Tuple[type]],
            ),
        ],
    ),
    "issubclass": (
        bool,
        [
            Parameter("class", Parameter.POSITIONAL_ONLY, annotation=type),
            Parameter(
                "classinfo",
                Parameter.POSITIONAL_ONLY,
                annotation=Union[type, Tuple[type]],
            ),
        ],
    ),
    "iter": (
        Iterator[T],  # type: ignore
        [
            Parameter(
                "object",
                Parameter.POSITIONAL_ONLY,
                annotation=Union[Iterable[T], Callable[[], T]],  # type: ignore
            ),
            Parameter("sentinel", Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
        ],
    ),
    "len": (int, [Parameter("s", Parameter.POSITIONAL_ONLY, annotation=Sized)]),
    "list": (
        List[T],  # type: ignore
        [
            Parameter(
                "iterable",
                Parameter.POSITIONAL_ONLY,
                Parameter.missing,
                Iterable[T],  # type: ignore
            )
        ],
    ),
    "locals": (dict, []),
    "map": (
        Iterator[T],  # type: ignore
        [
            Parameter(
                "function",
                Parameter.POSITIONAL_ONLY,
                annotation=Callable[..., T],  # type: ignore
            ),
            Parameter("iterables", Parameter.VAR_POSITIONAL, annotation=Iterable),
        ],
    ),
    "max": (
        Union[A, B],  # type: ignore
        [
            Parameter(
                "args",
                Parameter.VAR_POSITIONAL,
                annotation=Union[A, Iterable[A]],  # type: ignore
            ),
            Parameter(
                "key",
                Parameter.KEYWORD_ONLY,
                Parameter.missing,
                Optional[Callable[[A], Any]],  # type: ignore
            ),
            Parameter("default", Parameter.KEYWORD_ONLY, Parameter.missing, B),
        ],
    ),
    "memoryview": (
        memoryview,
        [Parameter("obj", Parameter.POSITIONAL_ONLY, annotation=ByteString)],
    ),
    "min": (
        Union[A, B],  # type: ignore
        [
            Parameter(
                "args",
                Parameter.VAR_POSITIONAL,
                annotation=Union[A, Iterable[A]],  # type: ignore
            ),
            Parameter(
                "key",
                Parameter.KEYWORD_ONLY,
                Parameter.missing,
                Optional[Callable[[A], Any]],  # type: ignore
            ),
            Parameter("default", Parameter.KEYWORD_ONLY, Parameter.missing, B),
        ],
    ),
    "next": (
        Union[A, B],  # type: ignore
        [
            Parameter(
                "iterator",
                Parameter.POSITIONAL_ONLY,
                annotation=Iterator[A],  # type: ignore
            ),
            Parameter("default", Parameter.POSITIONAL_ONLY, Parameter.missing, B),
        ],
    ),
    "object": (object, []),
    "oct": (str, [Parameter("x", Parameter.POSITIONAL_ONLY, annotation=int)]),
    "open": (
        typing.IO,
        [
            Parameter("file", Parameter.POSITIONAL_ONLY, annotation=FilePath),
            Parameter("mode", Parameter.POSITIONAL_OR_KEYWORD, "r", str),
            Parameter("buffering", Parameter.POSITIONAL_OR_KEYWORD, -1, int),
            Parameter("encoding", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
            Parameter("errors", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
            Parameter("newline", Parameter.POSITIONAL_OR_KEYWORD, None, Optional[str]),
            Parameter("closefd", Parameter.POSITIONAL_OR_KEYWORD, True, bool),
            Parameter(
                "opener",
                Parameter.POSITIONAL_OR_KEYWORD,
                None,
                Optional[Callable[[FilePath, int], typing.IO]],
            ),
        ],
    ),
    "ord": (int, [Parameter("c", Parameter.POSITIONAL_ONLY, annotation=str)]),
    "pow": (
        Number,
        [
            Parameter("base", Parameter.POSITIONAL_ONLY, annotation=Number),
            Parameter("exp", Parameter.POSITIONAL_ONLY, annotation=Number),
            Parameter("mod", Parameter.POSITIONAL_ONLY, Parameter.missing, Number),
        ],
    )
    if sys.version_info < (3, 8)
    else (
        Number,
        [
            Parameter("base", Parameter.POSITIONAL_OR_KEYWORD, annotation=Number),
            Parameter("exp", Parameter.POSITIONAL_OR_KEYWORD, annotation=Number),
            Parameter("mod", Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Number),
        ],
    ),
    "print": (
        None,
        [
            Parameter("objects", Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter("sep", Parameter.KEYWORD_ONLY, " ", Optional[str]),
            Parameter("end", Parameter.KEYWORD_ONLY, "\n", Optional[str]),
            Parameter("file", Parameter.KEYWORD_ONLY, sys.stdout, typing.TextIO),
            Parameter("flush", Parameter.KEYWORD_ONLY, False, bool),
        ],
    ),
    "property": (
        property,
        [
            Parameter(
                "fget",
                Parameter.POSITIONAL_OR_KEYWORD,
                None,
                Optional[Callable[[A], B]],  # type: ignore
            ),
            Parameter(
                "fset",
                Parameter.POSITIONAL_OR_KEYWORD,
                None,
                Optional[Callable[[A, B], Any]],  # type: ignore
            ),
            Parameter(
                "fdel",
                Parameter.POSITIONAL_OR_KEYWORD,
                None,
                Optional[Callable[[A], Any]],  # type: ignore
            ),
            Parameter("doc", Parameter.POSITIONAL_OR_KEYWORD, None, str),
        ],
    ),
    "range": (
        range,
        [
            Parameter("start_or_stop", Parameter.POSITIONAL_ONLY, annotation=int),
            Parameter("stop", Parameter.POSITIONAL_ONLY, Parameter.missing, int),
            Parameter("step", Parameter.POSITIONAL_ONLY, Parameter.missing, int),
        ],
    ),
    "repr": (str, [Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any)]),
    "reversed": (
        Iterator[T],  # type: ignore
        [
            Parameter("seq", Parameter.POSITIONAL_ONLY, annotation=Reversible[T]),  # type: ignore
        ],
    ),
    "round": (
        Number,
        [
            Parameter("number", Parameter.POSITIONAL_ONLY, annotation=Number),
            Parameter("ndigits", Parameter.POSITIONAL_ONLY, Parameter.missing, int),
        ],
    ),
    "set": (
        Set[T],  # type: ignore
        [
            Parameter(
                "iterable",
                Parameter.POSITIONAL_ONLY,
                Parameter.missing,
                Iterable[T],  # type: ignore
            )
        ],
    ),
    "setattr": (
        None,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("name", Parameter.POSITIONAL_ONLY, annotation=str),
            Parameter("value", Parameter.POSITIONAL_ONLY, annotation=Any),
        ],
    ),
    "slice": (
        slice,
        [
            Parameter("start_or_stop", Parameter.POSITIONAL_ONLY, annotation=int),
            Parameter("stop", Parameter.POSITIONAL_ONLY, Parameter.missing, int),
            Parameter("step", Parameter.POSITIONAL_ONLY, Parameter.missing, int),
        ],
    ),
    "sorted": (
        List[T],  # type: ignore
        [
            Parameter(
                "iterable",
                Parameter.POSITIONAL_ONLY,
                annotation=Iterable[T],  # type: ignore
            ),
            Parameter(
                "key",
                Parameter.KEYWORD_ONLY,
                None,
                Optional[Callable[[T], Any]],  # type: ignore
            ),
            Parameter("reverse", Parameter.KEYWORD_ONLY, False, bool),
        ],
    ),
    "staticmethod": (
        staticmethod,
        [Parameter("method", Parameter.POSITIONAL_ONLY, annotation=Any)],
    ),
    "str": (
        str,
        [
            Parameter("object", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("encoding", Parameter.POSITIONAL_OR_KEYWORD, "utf-8", str),
            Parameter("errors", Parameter.POSITIONAL_OR_KEYWORD, "strict", str),
        ],
    ),
    "sum": (
        Any,
        [
            Parameter("iterable", Parameter.POSITIONAL_ONLY, annotation=Iterable),
            Parameter("start", Parameter.POSITIONAL_ONLY, 0, Any),
        ],
    )
    if sys.version_info < (3, 8)
    else (
        Any,
        [
            Parameter("iterable", Parameter.POSITIONAL_ONLY, annotation=Iterable),
            Parameter("start", Parameter.POSITIONAL_OR_KEYWORD, 0, Any),
        ],
    ),
    "super": (
        super,
        [
            Parameter("type", Parameter.POSITIONAL_ONLY, Parameter.missing, type),
            Parameter("object_or_type", Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
        ],
    ),
    "tuple": (
        tuple,
        [Parameter("iterable", Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable)],
    ),
    "type": (
        type,
        [
            Parameter("object_or_name", Parameter.POSITIONAL_ONLY, annotation=Any),
            Parameter("bases", Parameter.POSITIONAL_ONLY, Parameter.missing, Tuple[type]),
            Parameter("dict", Parameter.POSITIONAL_ONLY, Parameter.missing, dict),
        ],
    ),
    "vars": (
        dict,
        [Parameter("object", Parameter.POSITIONAL_ONLY, Parameter.missing, Any)],
    ),
    "zip": (
        Iterator[tuple],
        [Parameter("iterables", Parameter.VAR_POSITIONAL, annotation=Iterable)]
        + (
            [Parameter("strict", Parameter.KEYWORD_ONLY, default=False, annotation=bool)]
            if sys.version_info >= (3, 10)
            else []
        ),
    ),
    "__import__": (
        types.ModuleType,
        [
            Parameter("name", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
            Parameter("globals", Parameter.POSITIONAL_OR_KEYWORD, None, Optional[dict]),
            Parameter("locals", Parameter.POSITIONAL_OR_KEYWORD, None, Optional[dict]),
            Parameter("fromlist", Parameter.POSITIONAL_OR_KEYWORD, (), Iterable),
            Parameter("level", Parameter.POSITIONAL_OR_KEYWORD, 0, int),
        ],
    ),
    "__build_class__": (
        type,
        [
            Parameter("func", Parameter.POSITIONAL_OR_KEYWORD, annotation=Callable),
            Parameter("name", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
            Parameter("bases", Parameter.VAR_POSITIONAL, annotation=type),
            Parameter(
                "metaclass",
                Parameter.KEYWORD_ONLY,
                None,
                Optional[Callable[[str, Tuple[type], dict], type]],
            ),
            Parameter("kwds", Parameter.VAR_KEYWORD, annotation=Any),
        ],
    ),
}
BUILTIN_SIGNATURES: Dict[Callable[..., object], Tuple[TypeAnnotation, List[Parameter]]] = {}
for key, value in _BUILTIN_SIGNATURES.items():
    try:
        key = getattr(builtins, key)
    except AttributeError:
        continue

    BUILTIN_SIGNATURES[key] = value
del _BUILTIN_SIGNATURES


class Signature(inspect.Signature):
    """
    An :class:`inspect.Signature` subclass that represents a function's parameter signature and return annotation.

    Instances of this class are immutable.

    :ivar parameters: An :class:`OrderedDict` of :class:`Parameter` objects
    :ivar return_annotation: The annotation for the function's return value
    """

    __slots__ = ()

    parameters: types.MappingProxyType[str, Parameter]  # type: ignore[reportIncompatibleMethodOverride]

    def __init__(
        self,
        parameters: Union[Iterable[Parameter], Mapping[str, Parameter], None] = None,
        return_annotation: Any = SIG_EMPTY,
        validate_parameters: bool = True,
    ):
        """
        :param parameters: A list or dict of :class:`Parameter` objects
        :param return_annotation: The annotation for the function's return value
        :param validate_parameters: Whether to check if the signature is valid
        """
        if return_annotation is SIG_EMPTY:
            return_annotation = inspect.Signature.empty

        if isinstance(parameters, collections.abc.Mapping):
            parameters = parameters.values()

        # Pyright is dumb and thinks the constructor only accepts Sequences
        parameters = cast(Sequence[Parameter], parameters)

        super().__init__(
            parameters,
            return_annotation=return_annotation,
            __validate_parameters__=validate_parameters,
        )

    @classmethod
    def from_signature(
        cls,
        signature: inspect.Signature,
    ) -> Self:
        """
        Creates a new ``Signature`` instance from an :class:`inspect.Signature`
        instance.

        .. versionchanged:: 1.4
            ``param_type`` parameter renamed to ``Parameter``.

        :param signature: An :class:`inspect.Signature` instance
        :param Parameter: The class to use for the signature's parameters
        :return: A new ``Signature`` instance
        """
        params = [Parameter.from_parameter(param) for param in signature.parameters.values()]
        return cls(params, return_annotation=signature.return_annotation)

    @classmethod
    def from_callable(
        cls,
        callable_: Callable[P, Any],
        *,
        follow_wrapped: bool = True,
        use_signature_db: bool = True,
    ) -> Self:
        """
        Returns a matching :class:`Signature` instance for the given ``callable_``.

        Because the signatures of builtin functions often cannot be determined
        (at least in older python versions), this function contains a database
        of signatures for builtin functions. These signatures contain much more
        detail than :func:`inspect.signature` would provide - like type annotations
        and default values of :attr:`Parameter.missing`.

        Pass ``use_signature_db=False`` if you wish to bypass the signature
        database.

        .. versionchanged:: 1.1
            Returns more accurate signatures for builtin functions.
            Also added missing "value" parameter for ``setattr``.

        .. versionadded:: 1.2
            Added ``use_signature_db`` parameter.

        .. versionchanged:: 1.2
            Signature database updated for python 3.9.

        .. versionchanged:: 1.4
            Signature database updated for python 3.10.
            ``param_type`` parameter renamed to ``Parameter``.

        :param callable_: A function or any other callable object
        :param Parameter: The class to use for the signature's parameters
        :param follow_wrapped: Whether to unwrap decorated callables
        :param use_signature_db: Whether to look up the signature
        :return: A corresponding ``Signature`` instance
        :raises InvalidArgumentType: If ``callable_`` isn't a callable object
        :raises NoSignatureFound: If the signature can't be determined (can
            happen for functions defined in C extensions)
        """
        is_bound_method = inspect.ismethod(callable_)
        if is_bound_method:
            callable_ = callable_.__func__  # type: ignore

        if follow_wrapped:
            callable_ = unwrap(callable_, lambda func: hasattr(func, "__signature__"))  # type: ignore

        if not callable(callable_):
            raise InvalidArgumentType("callable_", callable_, typing.Callable)

        if use_signature_db and callable_ in BUILTIN_SIGNATURES:
            ret_type, params = BUILTIN_SIGNATURES[callable_]
            params = [Parameter.from_parameter(param) for param in params]
            return cls(params, ret_type)

        try:
            sig = inspect.signature(callable_, follow_wrapped=False)
        except ValueError as error:
            # Callables written in C don't have an accessible signature.
            #
            # However, a ValueError can also be raised if `functools.partial` is
            # used to pass invalid arguments to a function, for example:
            #
            # partial(open, hello_kitty=True)
            if not str(error).startswith("no signature found"):
                raise
        else:
            # If we got a bound method as input, discard the first parameter
            if is_bound_method:
                parameters = [Parameter.from_parameter(param) for param in sig.parameters.values()]
                del parameters[0]
                return cls(parameters, sig.return_annotation)
            else:
                return cls.from_signature(sig)

        # Builtin exceptions also need special handling, but we don't want to
        # hard-code all of them in BUILTIN_SIGNATURES
        if isinstance(callable_, type) and issubclass(callable_, BaseException):
            return cls(
                [
                    Parameter("args", Parameter.VAR_POSITIONAL),
                ]
            )

        raise NoSignatureFound(callable_)

    @classmethod
    def for_method(
        cls,
        class_or_mro: Union[type, Iterable[type]],
        method_name: str,
    ) -> Self:
        """
        Creates a combined signature for the method in the given class and all
        parent classes, assuming that all `*args` and `**kwargs` are passed to
        the parent method.

        Example::

            class A:
                def method(self, foo: int = 3) -> None:
                    pass

            class B(A):
                def method(self, *args, bar: bool = True, **kwargs):
                    return super().method(*args, **kwargs)

            print(Signature.for_method(B, 'method'))
            # (self, foo: int = 3, *, bar: bool = True) -> None

        .. versionadded:: 1.5
        """
        if isinstance(class_or_mro, type):
            mro = static_mro(class_or_mro)
        else:
            mro = tuple(class_or_mro)

        return_annotation: TypeAnnotation = Signature.empty

        param_lists: List[List[Parameter]] = []
        for class_ in mro:
            class_vars = static_vars(class_)

            if method_name not in class_vars:
                continue

            method = cast(Callable[..., object], class_vars[method_name])
            signature = cls.from_callable(method)

            param_lists.append(signature.parameter_list)

            if return_annotation is Signature.empty:
                return_annotation = signature.return_annotation

        if not param_lists:
            raise MethodNotFound(method_name, class_or_mro)

        # Extract the "self" parameter from the first signature, if it has one
        self_param = []
        if param_lists[0]:
            param = param_lists[0][0]

            if param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                self_param = [param]

        positional_params: List[Parameter] = []
        keyword_params: List[Parameter] = []
        seen: Set[str] = set()  # Keep track of parameter names to avoid duplicates
        var_positional: Optional[Parameter] = None
        var_keyword: Optional[Parameter] = None

        for param_list in param_lists:
            var_positional = None
            var_keyword = None

            for param in param_list:
                # Skip the "self" parameter
                if param is param_list[0] and param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                    continue

                if param.name in seen:
                    continue
                seen.add(param.name)

                if param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                    positional_params.append(param)
                elif param.kind is Parameter.VAR_POSITIONAL:
                    var_positional = param
                elif param.kind is Parameter.KEYWORD_ONLY:
                    keyword_params.append(param)
                else:
                    var_keyword = param

        # If the last signature has varargs, don't ignore them
        if var_positional is not None:
            positional_params.append(var_positional)

        if var_keyword is not None:
            keyword_params.append(var_keyword)

        # Merge the parameters into a single list and make sure they all have a
        # valid kind
        parameters = self_param + positional_params + keyword_params

        max_kind: inspect._ParameterKind = Parameter.VAR_KEYWORD
        for i, param in renumerate(parameters):
            if param.kind < max_kind:
                max_kind = param.kind
            elif param.kind > max_kind:
                parameters[i] = param.replace(kind=max_kind)

        return cls(parameters, return_annotation=return_annotation)

    @property
    def parameter_list(self) -> List[Parameter]:
        """
        Returns a list of the signature's parameters.
        """
        return list(self.parameters.values())

    @property
    def positional_only_parameters(self) -> List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_ONLY`` parameters.
        """
        return [
            param for param in self.parameters.values() if param.kind is Parameter.POSITIONAL_ONLY
        ]

    @property
    def positional_and_keyword_parameters(self) -> List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_OR_KEYWORD`` parameters.
        """
        return [
            param
            for param in self.parameters.values()
            if param.kind is Parameter.POSITIONAL_OR_KEYWORD
        ]

    @property
    def keyword_only_parameters(self) -> List[Parameter]:
        """
        Returns a list of the signature's ``KEYWORD_ONLY`` parameters.
        """
        return [param for param in self.parameters.values() if param.kind is Parameter.KEYWORD_ONLY]

    @property
    def has_return_annotation(self) -> bool:
        """
        Returns whether the signature's return annotation is not :attr:`Signature.empty`.
        """
        return self.return_annotation is not Signature.empty

    @property
    def num_required_arguments(self) -> int:
        """
        Returns the number of required arguments, i.e. arguments with no default value.
        """
        return sum(not p.is_optional for p in self.parameters.values())

    def bind(self, *args: object, **kwargs: object) -> BoundArguments:
        """
        Similar to :meth:`inspect.Signature.bind`, but returns a
        :class:`introspection.BoundArguments` object.
        """
        bound_args = super().bind(*args, **kwargs)
        return BoundArguments.from_bound_arguments(bound_args)

    def bind_partial(self, *args: object, **kwargs: object) -> BoundArguments:
        """
        Similar to :meth:`inspect.Signature.bind_partial`, but returns a
        :class:`introspection.BoundArguments` object.
        """
        bound_args = super().bind_partial(*args, **kwargs)
        return BoundArguments.from_bound_arguments(bound_args)

    def with_new_parameter(self, index: int, parameter: Parameter) -> Self:
        """
        Returns a copy of this signature with a new parameter inserted.

        :param index: The index where the new parameter should be inserted
        :param parameter: The new parameter
        :return: A copy of this signature with the given parameter replaced
        """
        parameters = list(self.parameters.values())
        parameters.insert(index, parameter)
        return self.replace(parameters=parameters)

    def without_parameters(
        self,
        *params_to_remove: Union[int, str, inspect._ParameterKind],
    ) -> Self:
        """
        Returns a copy of this signature with some parameters removed.

        Parameters can be referenced by the following things:

        1. index
        2. name
        3. kind

        Example::

            >>> sig = Signature([
            ...     Parameter('foo'),
            ...     Parameter('bar'),
            ...     Parameter('baz'),
            ... ])
            >>> sig.without_parameters(0, 'baz')
            <Signature (bar)>

        .. versionchanged:: 1.5
            Parameters can now be referenced by kind.

        :param parameters: Names or indices of the parameters to remove
        :return: A copy of this signature without the given parameters
        """
        to_remove = set(params_to_remove)

        parameters: List[Parameter] = []

        for i, param in enumerate(self.parameters.values()):
            if i in to_remove or param.name in to_remove or param.kind in to_remove:
                continue

            parameters.append(param)

        return self.replace(parameters=parameters)

    def replace_varargs(
        self,
        parameters: Union[
            Callable[..., object],
            inspect.Signature,
            Iterable[inspect.Parameter],
            Mapping[str, inspect.Parameter],
        ],
    ) -> Self:
        """
        Replaces the ``*args`` and/or ``**kwargs`` parameters in this signature
        with the given parameters.

        If this signature has no ``*args``, the new parameters will be made
        ``KEYWORD_ONLY``. If it has no ``**kwargs``, they'll be made
        ``POSITIONAL_ONLY``.
        """
        if isinstance(parameters, inspect.Signature):
            parameters = parameters.parameters.values()
        elif isinstance(parameters, collections.abc.Mapping):
            parameters = parameters.values()
        elif isinstance(parameters, collections.abc.Iterable):
            pass
        else:
            parameters = type(self).from_callable(parameters).parameters.values()

        kinds = {p.kind for p in self.parameters.values()}
        has_varargs = Parameter.VAR_POSITIONAL in kinds
        has_varkwargs = Parameter.VAR_KEYWORD in kinds

        if not has_varargs and not has_varkwargs:
            raise ValueError("This signature has no VAR_POSITIONAL or VAR_KEYWORD parameter")

        # Replace *args with POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, and
        # VAR_POSITIONAL. Replace **kwargs with KEYWORD_ONLY and VAR_KEYWORD.
        replaces_args: List[inspect.Parameter] = []
        replaces_kwargs: List[inspect.Parameter] = []
        for parameter in parameters:
            # If we have *args but no **kwargs, we'll make all parameters
            # POSITIONAL_ONLY. Similarly, if we have **kwargs but no *args,
            # we'll make them all KEYWORD_ONLY.
            if parameter.kind is Parameter.POSITIONAL_OR_KEYWORD:
                if not has_varargs:
                    parameter = parameter.replace(kind=Parameter.KEYWORD_ONLY)
                elif not has_varkwargs:
                    parameter = parameter.replace(kind=Parameter.POSITIONAL_ONLY)

            if parameter.kind <= Parameter.VAR_POSITIONAL:
                replaces_args.append(parameter)
            else:
                replaces_kwargs.append(parameter)

        merged_parameters: List[Parameter] = []
        for parameter in self.parameters.values():
            if parameter.kind is Parameter.VAR_POSITIONAL:
                merged_parameters += map(Parameter.from_parameter, replaces_args)
            elif parameter.kind is Parameter.VAR_KEYWORD:
                merged_parameters += map(Parameter.from_parameter, replaces_kwargs)
            else:
                merged_parameters.append(parameter)

        return type(self)(merged_parameters, return_annotation=self.return_annotation)

    def to_string(
        self,
        implicit_typing: bool = False,
        indent: typing.Optional[int] = None,
    ) -> str:
        """
        Returns a string representation of this signature.

        Example::

            >>> Signature([
            ...    Parameter('nums', Parameter.VAR_POSITIONAL, annotation=int)
            ... ], return_annotation=int).to_string()
            '(*nums: int) -> int'

        :param implicit_typing: If ``True``, the "typing." prefix will be
            omitted from types defined in the ``typing`` module
        :return: A string representation of this signature, like you would see
            in python code
        """
        if indent is None:
            indent_str = ""
            sep = ", "
        else:
            indent_str = " " * indent
            sep = ",\n" + indent_str

        grouped_params = {
            kind: list(params)
            for kind, params in itertools.groupby(
                self.parameters.values(),
                key=lambda param: param.kind,
            )
        }

        text_chunks: List[str] = []  # When not empty, the last item must always be ``sep``

        # Positional-only parameters with a default value of ``missing`` need
        # special treatment, because they're displayed like [a[, b]]. Even
        # parameters with other default values are enclosed in these brackets:
        # [a, b=5[, c]]
        if Parameter.POSITIONAL_ONLY in grouped_params:
            brackets = 0

            for param in grouped_params.pop(Parameter.POSITIONAL_ONLY):
                param_str = param._to_string(implicit_typing, brackets_and_commas=False)

                if param.default is Parameter.missing:
                    if text_chunks:
                        del text_chunks[-1]
                        param_str = f"[{sep}{param_str}"
                    else:
                        param_str = f"[{param_str}"

                    brackets += 1

                text_chunks += [param_str, sep]

            if brackets:
                text_chunks.insert(-1, "]" * brackets)

            text_chunks += ["/", sep]

        for kind, params in grouped_params.items():
            if kind is Parameter.KEYWORD_ONLY:
                if Parameter.VAR_POSITIONAL not in grouped_params:
                    text_chunks += ["*", sep]

            for param in params:
                param_str = param._to_string(implicit_typing, brackets_and_commas=False)

                if param.default is Parameter.missing:
                    if text_chunks:
                        del text_chunks[-1]
                        param_str = f"[{sep}{param_str}]"
                    else:
                        param_str = f"[{param_str}]"

                text_chunks += [param_str, sep]

        if text_chunks:
            del text_chunks[-1]

            if indent is not None:
                text_chunks.insert(0, f"\n{indent_str}")
                text_chunks.append(",\n")

        params = "".join(text_chunks)

        if self.has_return_annotation:
            from .typing import annotation_to_string

            ann = annotation_to_string(self.return_annotation, implicit_typing=implicit_typing)
            ann = f" -> {ann}"
        else:
            ann = ""

        return f"({params}){ann}"

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        text = self.to_string()

        return "<{} {}>".format(cls_name, text)

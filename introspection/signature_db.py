import ast
import builtins
import os
import sys
import types
import typing
from numbers import Number
from typing_extensions import *
from typing import *

from .parameter import Parameter
from .signature_ import Signature
from .types import TypeAnnotation


__all__ = ["SIGNATURE_DB"]


T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
K = TypeVar("K")
V = TypeVar("V")
IntOrFloatVar = TypeVar("IntOrFloatVar", int, float)
FilePath = Union[str, bytes, os.PathLike[AnyStr]]


SIGNATURE_DB: Dict[Callable[..., object], Signature] = {}


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
                annotation=Literal["eval", "exec"],
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
        (
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
        )
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
        (
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
        )
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

for attr, (ret_type, params) in _BUILTIN_SIGNATURES.items():
    try:
        attr = getattr(builtins, attr)
    except AttributeError:
        continue

    SIGNATURE_DB[attr] = Signature(params, ret_type, forward_ref_context="builtins")

del _BUILTIN_SIGNATURES

import collections.abc
import contextlib  # NOT an unused import, your IDE is lying
import re  # NOT an unused import, your IDE is lying
import typing

from ._compat import LITERAL_TYPES
from .introspection import *
from . import introspection as typing_introspection
from ..types import Type_
from ..errors import *

__all__ = ["to_python", "to_typing"]


FORWARDREF_TO_TYPING = {
    "type": "Type",
    "list": "List",
    "tuple": "Tuple",
    "set": "Set",
    "frozenset": "Frozenset",
    "dict": "Dict",
    "str": "Text",
    "re.Pattern": "Pattern",
    "re.Match": "Match",
    "collections.deque": "Deque",
    "collections.defaultdict": "DefaultDict",
    "collections.Counter": "Counter",
    "collections.OrderedDict": "OrderedDict",
    "collections.ChainMap": "ChainMap",
    "collections.abc.Iterable": "Iterable",
    "collections.abc.Iterator": "Iterator",
    "collections.abc.Reversible": "Reversible",
    "collections.abc.Container": "Container",
    "collections.abc.Hashable": "Hashable",
    "collections.abc.Sized": "Sized",
    "collections.abc.Collection": "Collection",
    "collections.abc.Set": "AbstractSet",
    "collections.abc.MutableSet": "MutableSet",
    "collections.abc.Mapping": "Mapping",
    "collections.abc.MutableMapping": "MutableMapping",
    "collections.abc.Sequence": "Sequence",
    "collections.abc.MutableSequence": "MutableSequence",
    "collections.abc.ByteString": "ByteString",
    "collections.abc.MappingView": "MappingView",
    "collections.abc.KeysView": "KeysView",
    "collections.abc.ValuesView": "ValuesView",
    "collections.abc.ItemsView": "ItemsView",
    "collections.abc.Awaitable": "Awaitable",
    "collections.abc.Coroutine": "Coroutine",
    "collections.abc.AsyncIterable": "AsyncIterable",
    "collections.abc.AsyncIterator": "AsyncIterator",
    "collections.abc.Callable": "Callable",
    "contextlib.AbstractContextManager": "ContextManager",
    "contextlib.AbstractAsyncContextManager": "AsyncContextManager",
}

PYTHON_TO_TYPING = {}
for key, value in FORWARDREF_TO_TYPING.items():
    try:
        key = eval(key)
        value = getattr(typing, value)
    except AttributeError:
        continue

    PYTHON_TO_TYPING[key] = value


@typing.overload
def to_python(type_: Type_, strict: typing.Literal[True]) -> type:
    ...


@typing.overload
def to_python(type_: Type_, strict: bool = False) -> Type_:
    ...


def to_python(type_: Type_, strict: bool = False) -> Type_:
    """
    Given a ``typing`` type as input, returns the corresponding "regular" python
    class.

    Examples::

        >>> to_python(typing.List)
        <class 'list'>
        >>> to_python(typing.Iterable)
        <class 'collections.abc.Iterable'>

    Note that ``typing.Any`` and :class:`object` are two distinct types::

        >>> to_python(typing.Any)
        typing.Any
        >>> to_python(object)
        <class 'object'>

    Generics parameterized with ``typing.Any`` or other pointless constraints
    are converted to their regular python counterparts::

        >>> to_python(typing.List[typing.Any])
        <class 'list'>
        >>> to_python(typing.Callable[..., typing.Any])
        <class 'collections.abc.Callable'>
        >>> to_python(typing.Type[object])
        <class 'type'>

    The function recurses on the type arguments of parameterized generics::

        >>> to_python(typing.List[typing.Set], strict=False)
        typing.List[set]

    Forward references are handled, as well::

        >>> to_python(typing.List['Set'], strict=False)
        typing.List[set]

    :param type_: The type to convert to a python class
    :param strict: Whether to raise an exception if the input type has no python equivalent
    :return: The class corresponding to the input type
    """
    if type_ is None:
        return type_

    if not is_parameterized_generic(type_):
        if not is_typing_type(type_):
            return type_

        typ = typing_introspection._to_python(type_)

        # _to_python returns None if there's no equivalent
        if typ is not None:
            return typ
        elif not strict:
            return type_

        raise NoPythonEquivalent(type_)

    # At this point we know it's a parameterized generic type
    base = get_generic_base_class(type_)
    args = get_type_arguments(type_)

    if not is_variadic_generic(base) and all(arg is typing.Any for arg in args):
        return to_python(base, strict)
    elif base in (type, typing.Type) and args[0] is object:
        return type
    elif base in (collections.abc.Callable, typing.Callable) and args == (
        ...,
        typing.Any,
    ):
        return collections.abc.Callable

    # At this point we know that the type arguments aren't redundant, so if
    # python doesn't have a generic equivalent of the base type, then we can't
    # convert it
    py_base = to_python(base, strict=strict)

    # I don't think there is a single class that would fail this is_generic
    # check, so I'll just disable coverage for this
    if is_generic(py_base):  # pragma: no branch
        base = py_base
    elif strict:  # pragma: no cover
        raise NoGenericPythonEquivalent(type_)

    if base in (collections.abc.Callable, typing.Callable):
        if args[0] is ...:
            args = (..., to_python(args[1], strict))  # type: ignore
        else:
            args = (
                [to_python(arg, strict) for arg in args[0]],  # type: ignore
                to_python(args[1], strict),  # type: ignore
            )
    elif hasattr(typing, "Literal") and base is typing.Literal:
        return type_
    else:
        args = tuple(to_python(arg, strict) for arg in args)  # type: ignore

    # Some generics, like typing.Optional, don't accept tuples
    if len(args) == 1:
        args = args[0]

    return base[args]  # type: ignore


def to_typing(type_: Type_, strict: bool = False) -> Type_:
    """
    Given a python class as input, returns the corresponding
    ``typing`` annotation.

    Examples::

        >>> to_typing(list)
        typing.List
        >>> to_typing(typing.List[tuple])
        typing.List[typing.Tuple]
        >>> to_typing(typing.List['tuple'])
        typing.List[typing.Tuple]

    :param type_: The class to convert to a typing annotation
    :param strict: Whether to raise an exception if the input class has no ``typing`` equivalent
    :return: The corresponding annotation from the ``typing`` module
    """
    # process forward references
    if isinstance(type_, typing.ForwardRef):
        type_ = typing_introspection._get_forward_ref_code(type_)

    if isinstance(type_, str):
        try:
            type_ = FORWARDREF_TO_TYPING[type_]  # type: ignore
        except KeyError:
            pass

        if hasattr(typing, type_):  # type: ignore
            return getattr(typing, type_)  # type: ignore
    elif is_parameterized_generic(type_):
        base = to_typing(get_generic_base_class(type_), strict)
        args = get_type_arguments(type_)

        if base is typing.Callable:
            if args[0] is ...:
                args = (..., to_typing(args[1], strict))  # type: ignore
            else:
                args = (
                    [to_typing(arg, strict) for arg in args[0]],  # type: ignore
                    to_typing(args[1], strict),  # type: ignore
                )
        elif base in LITERAL_TYPES:
            return type_
        else:
            args = tuple(to_typing(arg, strict) for arg in args)  # type: ignore

        return base[args]  # type: ignore
    elif is_typing_type(type_):
        return type_
    else:
        try:
            return PYTHON_TO_TYPING[type_]
        except KeyError:
            pass

    if strict:
        raise NoTypingEquivalent(type_)  # type: ignore
    else:
        return type_

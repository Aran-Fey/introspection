
import collections.abc
import contextlib
import re
import typing

from .introspection import *
from .introspection import _to_python, _get_forward_ref_code, _is_variadic_generic
from . import _compat

__all__ = ['to_python', 'to_typing']


FORWARDREF_TO_TYPING = {
    # 'object': 'Any',
    'type': 'Type',
    'list': 'List',
    'tuple': 'Tuple',
    'set': 'Set',
    'frozenset': 'Frozenset',
    'dict': 'Dict',
    'str': 'Text',
    're.Pattern': 'Pattern',
    're.Match': 'Match',
    'collections.deque': 'Deque',
    'collections.defaultdict': 'DefaultDict',
    # 'collections.namedtuple': 'NamedTuple',
    'collections.Counter': 'Counter',
    'collections.OrderedDict': 'OrderedDict',
    'collections.ChainMap': 'ChainMap',
    'collections.abc.Iterable': 'Iterable',
    'collections.abc.Iterator': 'Iterator',
    'collections.abc.Reversible': 'Reversible',
    'collections.abc.Container': 'Container',
    'collections.abc.Hashable': 'Hashable',
    'collections.abc.Sized': 'Sized',
    'collections.abc.Collection': 'Collection',
    'collections.abc.Set': 'AbstractSet',
    'collections.abc.MutableSet': 'MutableSet',
    'collections.abc.Mapping': 'Mapping',
    'collections.abc.MutableMapping': 'MutableMapping',
    'collections.abc.Sequence': 'Sequence',
    'collections.abc.MutableSequence': 'MutableSequence',
    'collections.abc.ByteString': 'ByteString',
    'collections.abc.MappingView': 'MappingView',
    'collections.abc.KeysView': 'KeysView',
    'collections.abc.ValuesView': 'ValuesView',
    'collections.abc.ItemsView': 'ItemsView',
    'collections.abc.Awaitable': 'Awaitable',
    'collections.abc.Coroutine': 'Coroutine',
    'collections.abc.AsyncIterable': 'AsyncIterable',
    'collections.abc.AsyncIterator': 'AsyncIterator',
    'collections.abc.Callable': 'Callable',
    'contextlib.AbstractContextManager': 'ContextManager',
    'contextlib.AbstractAsyncContextManager': 'AsyncContextManager',
}

PYTHON_TO_TYPING = {}
for key, value in FORWARDREF_TO_TYPING.items():
    try:
        key = eval(key)
        value = getattr(typing, value)
    except AttributeError:
        continue

    PYTHON_TO_TYPING[key] = value


def to_python(type_, strict=False):
    """
    Given a ``typing`` type as input, returns the corresponding
    "regular" python class.

    Examples::

        >>> to_python(typing.List)
        <class 'list'>
        >>> to_python(typing.Iterable)
        <class 'collections.abc.Iterable'>

    Note that ``typing.Any`` and :class:`object` are two
    distinct types::

        >>> to_python(typing.Any)
        typing.Any
        >>> to_python(object)
        <class 'object'>

    Generics qualified with ``typing.Any`` or other pointless
    constraints are converted to their regular python
    counterparts::

        >>> to_python(typing.List[typing.Any])
        <class 'list'>
        >>> to_python(typing.Callable[..., typing.Any])
        <class 'collections.abc.Callable'>
        >>> to_python(typing.Type[object])
        <class 'type'>

    The function recurses on the type arguments of qualified
    generics::

        >>> to_python(typing.List[typing.Set], strict=False)
        typing.List[set]

    Forward references are handled, as well::

        >>> to_python(typing.List['Set'], strict=False)
        typing.List[set]

    :param type_: The type to convert to a python class
    :param strict: Whether to raise an exception if the input type has no python equivalent
    :return: The class corresponding to the input type
    """
    if isinstance(type_, type) and type_.__module__ != 'typing':
        return type_

    if type_ is None:
        return type_

    if not is_typing_type(type_, raising=False):
        raise TypeError("Expected a type, not {!r}".format(type_))

    if is_qualified_generic(type_):
        base = get_generic_base_class(type_)
        args = get_type_args(type_)

        if (not _is_variadic_generic(base)
                and all(arg is typing.Any for arg in args)):
            return to_python(base, strict)
        elif base is typing.Type and args[0] is object:
            return type
        elif base is typing.Callable and args == (..., typing.Any):
            return to_python(base, strict)

        if not strict:
            if base is typing.Callable:
                if args[0] is ...:
                    args = (..., to_python(args[1], strict))
                else:
                    args = (
                        [to_python(arg, strict) for arg in args[0]],
                        to_python(args[1], strict)
                    )
            elif hasattr(typing, 'Literal') and base is typing.Literal:
                return type_
            else:
                args = tuple(to_python(arg, strict) for arg in args)

            return base[args]
    else:
        typ = _to_python(type_)

        # _to_python returns None if there's no equivalent
        if typ is not None:
            return typ

    if strict:
        raise ValueError('{!r} has no python equivalent'.format(type_))
    else:
        return type_


def to_typing(type_, strict=False):
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
    if isinstance(type_, _compat.ForwardRef):
        type_ = _get_forward_ref_code(type_)

    if isinstance(type_, str):
        try:
            type_ = FORWARDREF_TO_TYPING[type_]
        except KeyError:
            pass

        if hasattr(typing, type_):
            return getattr(typing, type_)
    elif is_qualified_generic(type_):
        base = get_generic_base_class(type_)
        args = get_type_args(type_)

        if base is typing.Callable:
            if args[0] is ...:
                args = (..., to_typing(args[1], strict))
            else:
                args = (
                    [to_typing(arg, strict) for arg in args[0]],
                    to_typing(args[1], strict)
                )
        elif hasattr(typing, 'Literal') and base is typing.Literal:
            return type_
        else:
            args = tuple(to_typing(arg, strict) for arg in args)

        return base[args]
    elif is_typing_type(type_):
        return type_
    else:
        try:
            return PYTHON_TO_TYPING[type_]
        except KeyError:
            pass

    if strict:
        raise ValueError('{!r} has no typing equivalent'.format(type_))
    else:
        return type_

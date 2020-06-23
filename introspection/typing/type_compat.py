
import collections.abc
import contextlib
import re
import typing

from .introspection import is_typing_type, _to_python, _get_forward_ref_code
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
    'collections.defaultdict': 'defaultdict',
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

CLASS_TO_TYPING = {}
for key, value in FORWARDREF_TO_TYPING.items():
    try:
        key = eval(key)
        value = getattr(typing, value)
    except AttributeError:  # pragma: no cover
        continue

    CLASS_TO_TYPING[key] = value


def to_python(type_, strict=False):
    """
    Given a ``typing`` type as input, returns the corresponding
    "regular" python class.

    :param cls: The type to convert to a python class
    :param strict: Whether to raise an exception if the input type has no python equivalent
    :return: The class corresponding to the input type
    """

    if is_typing_type(type_, raising=False):
        typ = _to_python(type_)

        # _to_python returns None if there's no equivalent
        if typ is not None:
            return typ

        if not strict:
            return type_

        raise ValueError('{!r} has no python equivalent'.format(type_))

    if not isinstance(type_, type):
        raise TypeError("Expected a type, not {!r}".format(type_))

    if strict:
        raise ValueError('{!r} has no python equivalent'.format(type_))
    else:
        return type_


def to_typing(cls, strict=False):
    """
    Given a python class as input, returns the corresponding
    ``typing`` annotation.

    :param cls: The class to convert to a typing annotation
    :param strict: Whether to raise an exception if the input class has no ``typing`` equivalent
    :return: The corresponding annotation from the ``typing`` module
    """
    # process forward references
    if isinstance(cls, _compat.ForwardRef):
        cls = _get_forward_ref_code(cls)

    if isinstance(cls, str):
        try:
            return FORWARDREF_TO_TYPING[cls]
        except KeyError:
            pass
    else:
        try:
            return CLASS_TO_TYPING[cls]
        except KeyError:
            pass

    if strict:
        raise ValueError('{!r} has no typing equivalent'.format(cls))
    else:
        return cls

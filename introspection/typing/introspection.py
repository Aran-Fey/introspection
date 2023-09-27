from __future__ import annotations

import ordered_set

import sys
import types
import typing
import typing_extensions

from .i_hate_circular_imports import parameterize
from ..classes import safe_is_subclass
from ..types import Type_, GenericAliases
from ..errors import *

__all__ = [
    "is_type",
    "is_typing_type",
    "is_generic",
    "is_variadic_generic",
    "is_forwardref",
    "is_generic_base_class",
    "is_parameterized_generic",
    "is_fully_parameterized_generic",
    "get_generic_base_class",
    "get_type_arguments",
    "get_type_parameters",
    "get_type_argument_for",
    "get_type_name",
    "get_parent_types",
]


NoneType = type(None)


def _is_in(needle, haystack):
    try:
        return needle in haystack
    except TypeError:
        return False


def _resolve_dotted_name(name):
    """
    ::

        >>> resolve_dotted_name('collections.deque')
        <class 'collections.deque'>
    """
    module_name, *attrs = name.split(".")

    obj = sys.modules[module_name]
    for attr in attrs:
        obj = getattr(obj, attr)

    return obj


def _resolve_dotted_names(names):
    """
    ::

        >>> resolve_dotted_names({
        ...     'collections.deque': 'foo',
        ...     'collections.this_doesnt_exist': 'bar'
        ... })
        {<class 'collections.deque'>: 'foo'}
    """
    if isinstance(names, dict):
        result = {}

        for name, value in names.items():
            try:
                key = _resolve_dotted_name(name)
            except AttributeError:
                continue

            result[key] = value
    else:
        result = []

        for name in names:
            try:
                value = _resolve_dotted_name(name)
            except AttributeError:
                continue

            result.append(value)

        result = type(names)(result)

    return result


# NOTE: The following function implementations work in python 3.5.
# Depending on the python version being used, some of these functions
# will be overridden later.

T = typing.TypeVar("T")
K = typing.TypeVar("K")
V = typing.TypeVar("V")
T_co = typing.TypeVar("T_co", covariant=True)
K_co = typing.TypeVar("K_co", covariant=True)
V_co = typing.TypeVar("V_co", covariant=True)
Y_co = typing.TypeVar("Y_co", covariant=True)
A_co = typing.TypeVar("A_co", covariant=True)

VARIADIC_GENERICS = {
    "Union",
    "Tuple",
    "Literal",
}
VARIADIC_GENERICS = {
    getattr(typing, attr) for attr in VARIADIC_GENERICS if hasattr(typing, attr)
}

if sys.version_info >= (3, 9):
    VARIADIC_GENERICS.add(tuple)


def _is_variadic_generic(type_):
    return _is_in(type_, VARIADIC_GENERICS)


GENERIC_INHERITANCE = {
    "typing.Type": [("Generic", typing.TypeVar("CT_co", covariant=True))],
    "typing.Annotated": [("Generic", T_co)],
    "typing.ClassVar": [("Generic", T_co)],
    "typing.Final": [("Generic", T_co)],
    "typing.Optional": [("Generic", T_co)],
    "typing.Union": [("Generic", T_co)],
    "typing.Callable": [
        (
            "Generic",
            typing.TypeVar("A_contra", contravariant=True),
            typing.TypeVar("R_co", covariant=True),
        )
    ],
    "typing.Dict": [("MutableMapping", K, V)],
    "typing.DefaultDict": [("MutableMapping", K, V)],
    "typing.OrderedDict": [("MutableMapping", K, V)],
    "typing.ChainMap": [("MutableMapping", K, V)],
    "typing.Counter": [("MutableMapping", K, int)],
    "typing.Set": [("MutableSet", T)],
    "typing.FrozenSet": [("AbstractSet", T_co)],
    "typing.List": [("MutableSequence", T)],
    "typing.Deque": [("MutableSequence", T)],
    "typing.Tuple": [("Sequence", T_co)],
    "typing.Collection": [
        ("Sized",),
        ("Iterable", T_co),
        ("Container", T_co),
    ],
    "typing.Container": [("Generic", T_co)],
    "typing.Iterable": [("Generic", T_co)],
    "typing.Iterator": [("Iterable", T_co)],
    "typing.Reversible": [("Iterable", T_co)],
    "typing.Generator": [
        ("Iterator", Y_co),
        (
            "Generic",
            Y_co,
            typing.TypeVar("S_contra", contravariant=True),
            typing.TypeVar("R_co", covariant=True),
        ),
    ],
    "typing.ContextManager": [("Generic", T_co)],
    "typing.AsyncIterable": [("Generic", T_co)],
    "typing.AsyncIterator": [("AsyncIterable", T_co)],
    "typing.AsyncGenerator": [
        ("AsyncIterator", Y_co),
        ("Generic", Y_co, typing.TypeVar("S_contra", contravariant=True)),
    ],
    "typing.AsyncContextManager": [("Generic", T_co)],
    "typing.Coroutine": [
        ("Awaitable", A_co),
        ("Generic", T_co, typing.TypeVar("S_contra", contravariant=True), A_co),
    ],
    "typing.Awaitable": [("Generic", A_co)],
    "typing.AbstractSet": [
        ("Sized",),
        ("Collection", T_co),
    ],
    "typing.MutableSet": [("AbstractSet", T)],
    "typing.ByteString": [("Sequence", int)],
    "typing.ItemsView": [
        ("MappingView", typing.Tuple[K_co, V_co]),
        ("AbstractSet", typing.Tuple[K_co, V_co]),
    ],
    "typing.KeysView": [
        ("MappingView", K_co),
        ("AbstractSet", K_co, V_co),
    ],
    "typing.ValuesView": [
        ("MappingView", V_co),
    ],
    "typing.MappingView": [
        ("Sized",),
        ("Iterable", T_co),
    ],
    "typing.Mapping": [
        ("Collection", K),
        ("Generic", K, V),
    ],
    "typing.MutableMapping": [("Mapping", K, V)],
    "typing.Sequence": [
        ("Reversible", T_co),
        ("Collection", T_co),
    ],
    "typing.MutableSequence": [("Sequence", T)],
}
if sys.version_info >= (3, 9):
    GENERIC_INHERITANCE.update(
        {
            "builtins.tuple": GENERIC_INHERITANCE["typing.Tuple"],
            "builtins.list": GENERIC_INHERITANCE["typing.List"],
            "builtins.dict": GENERIC_INHERITANCE["typing.Dict"],
            "builtins.set": GENERIC_INHERITANCE["typing.Set"],
            "builtins.frozenset": GENERIC_INHERITANCE["typing.FrozenSet"],
            "builtins.type": GENERIC_INHERITANCE["typing.Type"],
            "collections.deque": GENERIC_INHERITANCE["typing.Deque"],
            "collections.defaultdict": GENERIC_INHERITANCE["typing.DefaultDict"],
            "collections.OrderedDict": GENERIC_INHERITANCE["typing.OrderedDict"],
            "collections.Counter": GENERIC_INHERITANCE["typing.Counter"],
            "collections.ChainMap": GENERIC_INHERITANCE["typing.ChainMap"],
            "collections.abc.Awaitable": GENERIC_INHERITANCE["typing.Awaitable"],
            "collections.abc.Coroutine": GENERIC_INHERITANCE["typing.Coroutine"],
            "collections.abc.AsyncIterable": GENERIC_INHERITANCE[
                "typing.AsyncIterable"
            ],
            "collections.abc.AsyncIterator": GENERIC_INHERITANCE[
                "typing.AsyncIterator"
            ],
            "collections.abc.AsyncGenerator": GENERIC_INHERITANCE[
                "typing.AsyncGenerator"
            ],
            "collections.abc.Iterable": GENERIC_INHERITANCE["typing.Iterable"],
            "collections.abc.Iterator": GENERIC_INHERITANCE["typing.Iterator"],
            "collections.abc.Generator": GENERIC_INHERITANCE["typing.Generator"],
            "collections.abc.Reversible": GENERIC_INHERITANCE["typing.Reversible"],
            "collections.abc.Container": GENERIC_INHERITANCE["typing.Container"],
            "collections.abc.Collection": GENERIC_INHERITANCE["typing.Collection"],
            "collections.abc.Callable": GENERIC_INHERITANCE["typing.Callable"],
            "collections.abc.Set": GENERIC_INHERITANCE["typing.AbstractSet"],
            "collections.abc.MutableSet": GENERIC_INHERITANCE["typing.MutableSet"],
            "collections.abc.Mapping": GENERIC_INHERITANCE["typing.Mapping"],
            "collections.abc.MutableMapping": GENERIC_INHERITANCE[
                "typing.MutableMapping"
            ],
            "collections.abc.Sequence": GENERIC_INHERITANCE["typing.Sequence"],
            "collections.abc.MutableSequence": GENERIC_INHERITANCE[
                "typing.MutableSequence"
            ],
            "collections.abc.ByteString": GENERIC_INHERITANCE["typing.ByteString"],
            "collections.abc.MappingView": GENERIC_INHERITANCE["typing.MappingView"],
            "collections.abc.KeysView": GENERIC_INHERITANCE["typing.KeysView"],
            "collections.abc.ItemsView": GENERIC_INHERITANCE["typing.ItemsView"],
            "collections.abc.ValuesView": GENERIC_INHERITANCE["typing.ValuesView"],
            "contextlib.AbstractContextManager": GENERIC_INHERITANCE[
                "typing.ContextManager"
            ],
            "contextlib.AbstractAsyncContextManager": GENERIC_INHERITANCE[
                "typing.AsyncContextManager"
            ],
            "re.Match": [("Generic", typing.AnyStr)],
            "re.Pattern": [("Generic", typing.AnyStr)],
        }
    )
GENERIC_INHERITANCE = _resolve_dotted_names(GENERIC_INHERITANCE)


PARAMETERIZED_GENERIC_META = (
    "types.GenericAlias",  # py3.9+
    "typing._GenericAlias",  # py3.8+
    "typing.GenericMeta",  # py3.5-3.7
)
PARAMETERIZED_GENERIC_META = _resolve_dotted_names(PARAMETERIZED_GENERIC_META)


def _get_type_parameters(type_):
    if sys.version_info >= (3, 10):
        if isinstance(type_, types.UnionType):
            return type_.__parameters__

    if safe_is_subclass(type_, typing.Generic):
        # Classes that inherit from Generic directly (like
        # ``class Protocol(Generic):``) and Generic itself don't
        # have __orig_bases__, while classes that have type
        # parameters do.
        if not hasattr(type_, "__orig_bases__"):
            return None

        return type_.__parameters__

    if isinstance(type_, PARAMETERIZED_GENERIC_META):
        if sys.version_info < (3, 7):
            # typing.Callable is an outlier that never has __orig_bases__
            if not type_.__orig_bases__ and type_._gorg is not typing.Callable:
                return None

        return type_.__parameters__

    if sys.version_info < (3, 7) and hasattr(typing, "_Union"):
        if isinstance(type_, typing._Union):
            return type_.__parameters__

    # Special case: ClassVar can only be parameterized once in older
    # versions
    if sys.version_info < (3, 7) and hasattr(typing, "_ClassVar"):
        if isinstance(type_, typing._ClassVar):
            return ()

    return None


PARAMLESS_SUBSCRIPTABLES = {
    typing.Generic,
    typing_extensions.Protocol,
    typing_extensions.Literal,
}


def _is_generic_base_class(cls):
    if isinstance(cls, (typing.CallableMeta, typing._Union)):
        return cls.__args__ is None

    if isinstance(cls, typing.GenericMeta):
        return cls.__args__ is None and bool(cls.__parameters__)

    if type(cls) is typing._ClassVar:
        return cls.__type__ is None

    return cls in {typing.Union, typing.Optional, typing.ClassVar}


def _is_parameterized_generic(cls):
    if isinstance(cls, (typing.GenericMeta, typing._Union)):
        return cls.__args__ is not None

    if type(cls) is typing._ClassVar:
        return cls.__type__ is not None

    return False


def _is_typing_type(cls):
    if not isinstance(cls, (typing.TypingMeta, typing._TypingBase)):
        return False

    if _is_parameterized_generic(cls):
        return True

    return cls.__module__ == "typing"


def _get_generic_base_class(cls):
    return cls.__origin__


def _to_python(cls):
    return getattr(cls, "__extra__", None)


def _get_name(cls):
    try:
        return cls.__name__
    except AttributeError:
        pass

    typing_, _, name = repr(cls).partition(".")
    return name


if sys.version_info >= (3, 7):
    SPECIAL_GENERICS = {typing.Optional, typing.Union, typing.ClassVar, typing.Callable}

    if hasattr(typing, "Literal"):  # python 3.8+
        SPECIAL_GENERICS.add(typing.Literal)

    if hasattr(typing, "Final"):  # python 3.8+
        SPECIAL_GENERICS.add(typing.Final)

    def _is_parameterized_generic(cls):
        if isinstance(cls, typing._GenericAlias):
            return not cls._special

        return False

    def _is_generic_base_class(cls):
        if isinstance(cls, typing._GenericAlias):
            # The _special attribute was removed in 3.9
            if not cls._special:
                return False
        elif not isinstance(cls, (type, typing._SpecialForm)):
            return False

        return is_generic(cls)

    def _is_typing_type(cls):
        if isinstance(cls, typing._GenericAlias):
            return True

        if sys.version_info >= (3, 10):
            if cls is types.UnionType or isinstance(cls, types.UnionType):
                return True

        try:
            module = cls.__module__
        except AttributeError:
            return False

        return module == "typing"

    def _get_generic_base_class(cls):
        if cls._name is not None:
            return getattr(typing, cls._name)

        return cls.__origin__

    def _to_python(cls):
        return getattr(cls, "__origin__", None)

    def _get_name(cls):
        try:
            return cls.__name__
        except AttributeError:
            return cls._name


if sys.version_info >= (3, 9):

    def _is_generic_base_class(cls):
        if safe_is_subclass(cls, typing.Generic):
            return bool(cls.__parameters__)

        return False

    def _is_parameterized_generic(cls):
        if sys.version_info >= (3, 10) and isinstance(cls, types.UnionType):
            return True

        return isinstance(cls, (types.GenericAlias, typing._GenericAlias))

    def _get_generic_base_class(cls):
        if isinstance(cls, typing._GenericAlias):
            if cls._name is not None:
                return getattr(typing, cls._name)

            if isinstance(cls, typing._AnnotatedAlias):
                return typing.Annotated

        if sys.version_info >= (3, 10) and isinstance(cls, types.UnionType):
            return typing.Union

        return cls.__origin__


if hasattr(typing, "get_args"):  # python 3.8+

    def _get_type_args(cls):
        return typing.get_args(cls)

else:
    if hasattr(typing.Union, "_subs_tree"):  # python <3.7

        def _get_base_and_args(cls):
            # In older python versions, generics only store the
            # last pair of arguments. For instance,
            #    >>> Tuple[List[T]][int].__args__
            #    (int,)
            # The output we want is (List[int],).
            # The _subs_tree() method can help us out - it
            # returns a tuple that we can use to construct
            # the output we want:
            #    >>> Tuple[List[T]][int]._subs_tree()
            #    (typing.Tuple, (typing.List, <class 'int'>))
            base_generic, *subtypes = cls._subs_tree()

            def tree_to_type(tree):
                if isinstance(tree, tuple):
                    subtypes = tuple(tree_to_type(t) for t in tree[1:])
                    return tree[0][subtypes]

                return tree

            subtypes = tuple(map(tree_to_type, subtypes))

            return base_generic, subtypes

    else:  # python 3.7

        def _get_base_and_args(cls):
            return _get_generic_base_class(cls), cls.__args__

    def _get_type_args(cls):
        base_generic, subtypes = _get_base_and_args(cls)

        if base_generic == typing.Callable:
            if subtypes[0] is not ...:
                subtypes = (list(subtypes[:-1]), subtypes[-1])

        return subtypes


def _get_forward_ref_code(ref):
    return ref.__forward_arg__


def _is_regular_type(type_):
    if isinstance(type_, type):
        return True

    if type_ is None:
        return True

    return False


def is_forwardref(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a forward reference.

    Examples::

        >>> is_forwardref('List')
        True
        >>> is_forwardref(typing.ForwardRef('List'))
        True
        >>> is_forwardref(List)
        False

    .. versionadded:: 1.2

    :param type_: The object to examine
    :param raising: Whether to throw a :exc:`NotAType` exception if ``type_`` is not a type
    :return: Whether the object is a class or type (or forward reference)
    """
    if isinstance(type_, (str, typing.ForwardRef)):
        return True

    if raising and not is_type(type_):
        raise NotAType("type_", type_)

    return False


def is_type(type_: typing.Any, allow_forwardref: bool = True) -> bool:
    """
    Returns whether ``type_`` is a type - i.e. something that is a valid type annotation.

    Examples::

        >>> is_type(int)
        True
        >>> is_type(None)
        True
        >>> is_type(typing.List)
        True
        >>> is_type(typing.List[str])
        True
        >>> is_type('Foo')  # this is a forward reference
        True
        >>> is_type(3)
        False

    .. versionadded:: 1.2
       The ``allow_forwardref`` parameter.

    :param type_: The object to examine
    :param allow_forwardref: Controls whether strings and ForwardRefs are considered types
    :return: Whether the object is a class or type (or forward reference)
    """
    # strings are forward references
    if isinstance(type_, (str, typing.ForwardRef)):
        return allow_forwardref

    if isinstance(type_, GenericAliases):
        return True

    if _is_regular_type(type_):
        return True

    return is_typing_type(type_, raising=False)


def is_typing_type(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a type added by :pep:`0484`.
    This includes parameterized generics and all types defined in
    the :mod:`typing` module (but not custom subclasses thereof)
    *except* for :class:`typing.ForwardRef`.

    If ``type_`` is not a type as defined by :func:`~introspection.typing.is_type`
    and ``raising`` is ``True``, a :exc:`NotAType` exception is raised.
    (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` if ``type_`` is not a type
    :return: Whether the object is a ``typing`` type
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if is_forwardref(type_, raising=False):
        return False

    if _is_typing_type(type_):
        return True

    if isinstance(type_, typing.TypeVar):
        return True

    if not raising or _is_regular_type(type_):
        return False

    raise NotAType("type_", type_)


def is_generic(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is any kind of generic type, for example ``List``,
    ``List[T]`` or even ``List[Tuple[T]]``. This includes "special" types like
    ``Union``, ``Tuple`` and ``Literal`` - anything that's subscriptable is
    considered generic.

    If ``type_`` is not a type as defined by
    :func:`~introspection.typing.is_type` and ``raising`` is ``True``,
    :exc:`NotAType` is raised. (Otherwise, ``False`` is returned.)

    .. versionchanged:: 1.6
        This function now returns ``True`` for :class:`typing.Generic` and
        `typing.Protocol`.

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` if ``type_`` is not a type
    :return: Whether the object is a generic type
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """

    try:
        params = get_type_parameters(type_)
    except NotAGeneric:
        return _is_in(type_, PARAMLESS_SUBSCRIPTABLES)
    except NotAType:
        if raising:
            raise

        return False

    return bool(params)


def is_variadic_generic(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a generic type that accepts an
    arbitrary number of type arguments. (e.g. ``Union``, ``Tuple``,
    ``Literal``, etc.)

    If ``type_`` is not a type as defined by
    :func:`~introspection.typing.is_type` and ``raising`` is ``True``,
    :exc:`NotAType` is raised. (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` if ``type_`` is not a type
    :return: Whether the object is a variadic generic type
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if not is_type(type_):
        if raising:
            raise NotAType("type_", type_) from None
        else:
            return False

    return _is_variadic_generic(type_)


def is_generic_base_class(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a generic base class,
    for example ``List`` (but not ``List[int]`` or
    ``List[T]``).

    If ``type_`` is not a type as defined by
    :func:`~introspection.typing.is_type` and ``raising`` is ``True``,
    :exc:`NotAType` is raised. (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` on invalid input
    :return: Whether the object is a generic class with no type arguments
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if _is_in(type_, PARAMLESS_SUBSCRIPTABLES):
        return True

    if not is_generic(type_, raising=raising):
        return False

    if _is_in(type_, GENERIC_INHERITANCE):
        return True

    if _is_generic_base_class(type_):
        return True

    return False


def is_parameterized_generic(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a generic type with some
    type arguments supplied, for example ``List[int]``
    or ``List[T]`` (but not ``List``) - in other words, a
    :class:`types.GenericAlias`.

    If ``type_`` is not a type as defined by
    :func:`~introspection.typing.is_type` and ``raising`` is ``True``,
    :exc:`NotAType` is raised. (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` on invalid input
    :return: Whether the object is a generic type with type arguments
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if not is_type(type_):
        if raising:
            raise NotAType("type_", type_)

        return False

    return _is_parameterized_generic(type_)


def is_fully_parameterized_generic(type_: Type_, raising: bool = True) -> bool:
    """
    Returns whether ``type_`` is a generic type with all type arguments
    supplied, for example ``List[int]`` (but not ``List[T]`` or
    ``List[Tuple[T]]``).

    Unlike :func:`is_parameterized_generic`, which will only ever return
    ``True`` for :class:`types.GenericAlias` objects, this function returns
    ``True`` for any input that was once generic, but no longer accepts
    any more type parameters. For example::

        >>> is_parameterized_generic(typing.ByteString)
        False
        >>> is_fully_parameterized_generic(typing.ByteString)
        True

    If ``type_`` is not a type as defined by
    :func:`~introspection.typing.is_type` and ``raising`` is ``True``,
    :exc:`NotAType` is raised. (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw :exc:`NotAType` on invalid input
    :return: Whether the object is a generic type with type arguments
    :raises NotAType: If ``type_`` is not a type and ``raising`` is ``True``
    """
    try:
        return get_type_parameters(type_) == ()
    except ValueError:
        return False
    except NotAType:
        if raising:
            raise

        return False


def get_generic_base_class(type_: Type_) -> Type_:
    """
    Given a parameterized generic type as input, returns the corresponding
    generic base class.

    Example::

        >>> get_generic_base_class(typing.List[int])
        typing.List

    .. versionchanged:: 1.5.1
        Now throws :exc:`ValueError` instead of :exc:`TypeError` if the input is
        a type, but not generic.

    :param type_: A parameterized generic type
    :return: The input type without its type arguments
    :raises NotAParameterizedGeneric: If the input isn't a parameterized generic
    """
    if not is_parameterized_generic(type_, raising=True):
        raise NotAParameterizedGeneric("type_", type_)

    base = _get_generic_base_class(type_)

    # typing.Optional is a special case that turns into a typing.Union[X, None]
    if base is typing.Union:
        args = _get_type_args(type_)

        args = tuple(arg for arg in args if arg not in {None, NoneType})

        if len(args) == 1:
            base = typing.Optional

    return base


def get_type_arguments(type_: Type_) -> typing.Tuple[object]:
    """
    Given a parameterized generic type as input, returns a tuple of its type
    arguments.

    Example::

        >>> get_type_arguments(typing.List[int])
        (<class 'int'>,)
        >>> get_type_arguments(typing.Callable[[str], None])
        ([<class 'str'>], None)

    Note that some generic types (like :any:`typing.Optional`) won't accept a
    tuple as input, so take care when you try to parameterize something with
    this function's return value::

        >>> get_type_arguments(typing.Optional[int])
        (<class 'int'>,)
        >>> typing.Optional[(int,)]
        TypeError: typing.Optional requires a single type. Got (<class 'int'>,).

    .. versionchanged:: 1.5.1
        Now throws :exc:`ValueError` instead of :exc:`TypeError` if the input is
        a type, but not generic.

    :param type_: A parameterized generic type
    :return: The input type's type arguments
    """
    if not is_parameterized_generic(type_, raising=True):
        raise NotAParameterizedGeneric("type_", type_)

    args = _get_type_args(type_)

    # typing.Optional is a special case that turns into a typing.Union[X, None],
    # so if this type's base is Union and it there's only one type argument
    # that isn't NoneType, we'll only return that one type argument. This
    # guarantees that the returned arguments are compatible with the output
    # of get_generic_base_class.
    base = _get_generic_base_class(type_)
    if base in (typing.Union, typing.Optional):
        cleaned_args = tuple(arg for arg in args if arg not in {None, NoneType})

        if len(cleaned_args) == 1:
            args = cleaned_args

    return args


def get_type_parameters(type_: Type_) -> typing.Tuple[typing.TypeVar]:
    """
    Returns the TypeVars of a generic type.

    If ``type_`` is not a type, :exc:`NotAType` is raised.

    If ``type_`` is a type, but not generic, :exc:`NotAGeneric` is raised.

    If ``type_`` is a fully parameterized generic class (like
    :class:`typing.ByteString`), an empty tuple is returned.

    Examples::

        >>> get_type_parameters(List)
        (~T,)
        >>> get_type_parameters(Generator)
        (+T_co, -T_contra, +V_co)
        >>> get_type_parameters(List[Tuple[T, int, T]])
        (~T,)
        >>> get_type_parameters(ByteString)
        ()

    In most cases, the returned TypeVars correspond directly to the type
    parameters the type accepts. However, some special cases exist. Firstly,
    there are generics which accept any number of type arguments, like
    ``Tuple``. Calling ``get_type_parameters`` on these will only return a
    single ``TypeVar``::

        >>> get_type_parameters(Union)
        (+T_co,)
        >>> get_type_parameters(Tuple)
        (+T_co,)

    Secondly, there are special generic types that the ``typing`` module
    internally doesn't implement with TypeVars. Despite this,
    ``get_type_parameters`` still supports them::

        >>> get_type_parameters(Optional)
        (+T_co,)
        >>> get_type_parameters(ClassVar)
        (+T_co,)
        >>> get_type_parameters(Callable)
        (-A_contra, +R_co)

    .. versionchanged:: 1.2
        Now throws :exc:`ValueError` instead of :exc:`TypeError` if the
        input is a type, but not generic.

    :raises NotAType: If ``type_`` is not a type
    :raises NotAGeneric: If ``type_`` is a type, but not generic
    """
    if not is_type(type_):
        raise NotAType("type_", type_)

    try:
        bases = GENERIC_INHERITANCE[type_]
    except (KeyError, TypeError):
        pass
    else:
        params = ordered_set.OrderedSet()

        for base, *typevars in bases:
            params.update(typevars)

        return tuple(param for param in params if isinstance(param, typing.TypeVar))

    params = _get_type_parameters(type_)

    if params is not None:
        return params

    raise NotAGeneric("type_", type_)


def get_type_argument_for(
    type_: Type_,
    base_type: Type_,
    type_var: typing.Optional[typing.TypeVar] = None,
    *,
    assume_any: bool = True,
    allow_typevar: bool = False,
) -> Type_:
    """
    Returns the value of a specific TypeVar, given a parameterized type and a
    generic type as input.

    Example::

        class GenericIO(typing.Generic[I,O]):
            ...

        class StrToBytesIO(GenericIO[str,bytes]):
            ...

        assert get_type_argument_for(StrToBytesIO, GenericIO, I) == str
        assert get_type_argument_for(StrToBytesIO, GenericIO, O) == bytes

    If the generic type only has 1 TypeVar, the ``type_var`` argument can be
    omitted::

        >>> get_type_argument_for(list[int], collections.abc.Iterable)
        <class 'int'>

    If the TypeVar doesn't have a value and ``assume_any`` is ``True``,
    ``typing.Any`` is returned. If ``assume_any`` is ``False``, a
    :exc:`ValueError` is raised instead. Example::

        from collections.abc import Sequence

        class MySequence(Sequence):
            ...

        assert get_type_argument_for(MySequence, Sequence, assume_any=True) is typing.Any

    If the value of the TypeVar is another TypeVar and ``allow_typevar`` is
    ``False``, a :exc:`ValueError` is raised. If ``allow_typevar`` is ``True``,
    the TypeVar is returned instead. Example::

        >>> get_type_argument_for(list[T], list, allow_typevar=True)
        T

    .. versionadded:: 1.6
    """
    # We'll climb the inheritance tree until we reach base_type, keeping track
    # of all the type parameters and arguments in our stack. For example, if the
    # class hierarchy is:
    #
    #     class Foo(Generic[A,B]): ...
    #     class Bar(Foo[int,T]): ...
    #     class Qux(Bar[str]): ...
    #
    # then the stack for type_=Qux and base_type=Foo will be:
    #
    #     [
    #          ([T], [str]),
    #          ([A,B], [int,T]),
    #     ]
    #
    # Once the stack is complete, we loop over it backwards while keeping track
    # of the current value of our TypeVar. For example, if type_var=B:
    #
    # 1. The argument for type_var=B is T. Since T is a TypeVar, we set
    #    type_var=T and continue.
    # 2. The argument for type_var=T is str. Since this isn't a TypeVar, we
    #    return str.
    stack = []

    if is_parameterized_generic(type_):
        cls = get_generic_base_class(type_)

        args = get_type_arguments(type_)
        params = get_type_parameters(cls)

        stack.append((params, args))
    else:
        cls = type_

    while cls is not base_type:
        # Find a parent class that inherits from base_type. (If there's more
        # than one such class, it shouldn't matter which one we pick.)
        for base in get_parent_types(cls):
            if is_parameterized_generic(base):
                cls = get_generic_base_class(base)
                if not safe_is_subclass(cls, base_type):
                    continue

                args = get_type_arguments(base)
                break
            elif safe_is_subclass(base, base_type):
                cls = base
                args = ()
                break
        else:
            raise SubTypeRequired(type_, base_type)

        params = get_type_parameters(cls)
        stack.append((params, args))

    if type_var is None:
        params, _ = stack[-1]

        if len(params) > 1:
            raise ArgumentRequired(
                "type_var", reason=f"{base_type!r} has more than 1 TypeVar"
            )

        type_var = params[0]

    current_var = type_var

    for params, args in reversed(stack):
        i = params.index(current_var)

        try:
            arg = args[i]
        except IndexError:
            if assume_any:
                return typing.Any

            raise TypeVarNotSet(type_var, base_type, type_)

        if not isinstance(arg, typing.TypeVar):
            return arg

        current_var = arg

    if not allow_typevar:
        raise NoConcreteTypeForTypeVar(type_var, base_type, type_, current_var)

    return current_var


def get_type_name(type_: Type_) -> str:
    """
    Returns the name of a type.

    Examples::

        >>> get_type_name(list)
        'list'
        >>> get_type_name(typing.List)
        'List'

    :param type_: The type whose name to retrieve
    :return: The type's name
    :raises NotAType: If ``type_`` isn't a type
    :raises GenericMustNotBeParameterized: If ``type_`` is a parameterized
        generic type
    :raises ForwardRefsDontHaveNames: If ``type_`` is a forward reference
    """
    if not is_type(type_):
        raise NotAType("type_", type_)

    if isinstance(type_, str):
        raise ForwardRefsDontHaveNames("type_", type_)

    if is_parameterized_generic(type_, raising=False):
        raise GenericMustNotBeParameterized("type_", type_)

    if type_ is None:
        type_ = type(type_)

    return _get_name(type_)


def get_parent_types(type_: Type_) -> typing.Tuple[Type_]:
    """
    Given a type as input, returns a tuple of its parent types - including type
    arguments, if it's a generic type.

    Examples::

        >>> get_parent_types(int)
        (<class 'float'>,)
        >>> get_parent_types(re.Pattern)
        (typing.Generic[typing.AnyStr],)

    .. versionadded: 1.6
    """
    if type_ is int:
        return (float,)

    if type_ in GENERIC_INHERITANCE:
        base, *type_vars = GENERIC_INHERITANCE[type_]
        return (parameterize(base, type_vars),)

    # When inheriting from a parameterized type, like
    #
    #   class Child(Parent[int]):
    #
    # then `__bases__` only contains `Parent`. To find `Parent[int]`, we have to
    # look in `__orig_bases__`. *However*, when inheriting from a generic type
    # without parameterizing it, then `__orig_bases__` will contain `Generic`
    # for some godforsaken reason.
    try:
        orig_bases = type_.__orig_bases__
    except AttributeError:
        return type_.__bases__

    parent_types = []

    for base, orig_base in zip(type_.__bases__, orig_bases):
        # Non-generic types show up as-is in both tuples
        if base is orig_base:
            parent_types.append(base)
        else:
            generic_base = get_generic_base_class(orig_base)
            if base is generic_base:
                parent_types.append(orig_base)
            else:
                # If they're different, that means it's a generic class with no
                # type arguments provided. Which means the arguments are all
                # typing.Any.
                params = get_type_parameters(base)
                parameterized_base = parameterize(base, [typing.Any] * len(params))
                parent_types.append(parameterized_base)

    return tuple(parent_types)

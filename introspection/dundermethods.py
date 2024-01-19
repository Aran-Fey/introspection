import types
from typing import Iterator, Iterable, Tuple, Dict, Any, Callable, Optional, Type

from .classes import static_mro
from .misc import static_vars
from .errors import *

__all__ = [
    "DUNDERMETHOD_NAMES",
    "AUGMENTED_ASSIGNMENT_DUNDERMETHOD_NAMES",
    "iter_class_dundermethods",
    "class_implements_dundermethod",
    "class_implements_any_dundermethod",
    "class_implements_dundermethods",
    "collect_class_dundermethods",
    "get_class_dundermethod",
    "get_bound_dundermethod",
    "call_dundermethod",
]


# An incomplete(!) list of dundermethods can be found on the data model page:
# https://docs.python.org/3/reference/datamodel.html
#: A set containing the names of all dundermethods available in python 3.9.
DUNDERMETHOD_NAMES = {
    "__abs__",
    "__add__",
    "__aenter__",
    "__aexit__",
    "__aiter__",
    "__and__",
    "__anext__",
    "__await__",
    "__bool__",
    "__bytes__",
    "__call__",
    "__complex__",
    "__contains__",
    "__delattr__",
    "__delete__",
    "__delitem__",
    "__delslice__",
    "__dir__",
    "__div__",
    "__divmod__",
    "__enter__",
    "__eq__",
    "__exit__",
    "__float__",
    "__floordiv__",
    "__format__",
    "__fspath__",
    "__ge__",
    "__get__",
    "__getattribute__",
    "__getitem__",
    "__getnewargs__",
    "__getslice__",
    "__gt__",
    "__hash__",
    "__iadd__",
    "__iand__",
    "__imul__",
    "__index__",
    "__init__",
    "__init_subclass__",
    "__instancecheck__",
    "__int__",
    "__invert__",
    "__ior__",
    "__isub__",
    "__iter__",
    "__ixor__",
    "__le__",
    "__len__",
    "__lshift__",
    "__lt__",
    "__mod__",
    "__mul__",
    "__ne__",
    "__neg__",
    "__new__",
    "__next__",
    "__or__",
    "__pos__",
    "__pow__",
    "__prepare__",
    "__radd__",
    "__rand__",
    "__rdiv__",
    "__rdivmod__",
    "__reduce__",
    "__reduce_ex__",
    "__repr__",
    "__reversed__",
    "__rfloordiv__",
    "__rlshift__",
    "__rmod__",
    "__rmul__",
    "__ror__",
    "__round__",
    "__rpow__",
    "__rrshift__",
    "__rshift__",
    "__rsub__",
    "__rtruediv__",
    "__rxor__",
    "__set__",
    "__setattr__",
    "__setitem__",
    "__sizeof__",
    "__str__",
    "__sub__",
    "__subclasscheck__",
    "__subclasses__",
    "__truediv__",
    "__xor__",
    "__rmatmul__",
    "__imatmul__",
    "__ifloordiv__",
    "__class_getitem__",
    "__irshift__",
    "__floor__",
    "__ilshift__",
    "__length_hint__",
    "__del__",
    "__matmul__",
    "__ipow__",
    "__getattr__",
    "__set_name__",
    "__ceil__",
    "__imod__",
    "__itruediv__",
    "__trunc__",
}

#: A set containing the names of all augmented assignment dundermethods
#: available in python 3.9.
#:
#: .. versionadded:: 1.1
AUGMENTED_ASSIGNMENT_DUNDERMETHOD_NAMES = {
    "__iadd__",
    "__isub__",
    "__imul__",
    "__imatmul__",
    "__itruediv__",
    "__ifloordiv__",
    "__imod__",
    "__ipow__",
    "__ilshift__",
    "__irshift__",
    "__iand__",
    "__ixor__",
    "__ior__",
}

#: A set containing the names of all dundermethods for which ``None`` is
#: a valid value in python 3.9.
#:
#: .. versionadded:: 1.4
NONEABLE_DUNDERMETHOD_NAMES = {
    "__hash__",
    "__iter__",
}


def _is_implemented(name, method):
    if name in NONEABLE_DUNDERMETHOD_NAMES:
        return method is not None
    else:
        return True


def iter_class_attributes(
    cls: type,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> Iterator[Tuple[str, Any]]:
    mro = static_mro(cls)

    if start is not None:
        if start_after is not None:
            raise ConflictingArguments("start", "start_after")

        mro = mro[mro.index(start) :]
    elif start_after is not None:
        mro = mro[mro.index(start_after) + 1 :]

    if bound is not None:
        mro = mro[: mro.index(bound)]

    for cls in mro:
        yield from static_vars(cls).items()


def iter_class_dundermethods(
    cls: type,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> Iterator[Tuple[str, Any]]:
    """
    Yields all dundermethods implemented by the given class as
    ``(method_name, method)`` tuples.

    (For the purpose of this function, "implemented" simply means "exists". Even
    if the method's value is ``None`` or anything else, it will still be
    yielded.)

    If multiple classes in the MRO implement the same dundermethod, both methods
    will be yielded. Methods implemented by subclasses will always be yielded
    before methods implemented by parent classes.

    You can skip some classes in the MRO by specifying ``start`` or
    ``start_after``. If ``start`` is not ``None``, iteration will begin at that
    class. If ``start_after`` is not ``None``, iteration will begin after that
    class. Passing both at the same time is not allowed.

    You can cause the iteration to stop early by passing in a class as the upper
    ``bound``. The MRO will only be iterated up to the ``bound``, excluding the
    ``bound`` class itself. This is useful for excluding dundermethods
    implemented in :class:`object`.

    :param cls: The class whose dundermethods to yield
    :param start: Where to start iterating through the class's MRO
    :param start_after: Where to start iterating through the class's MRO
    :param bound: Where to stop iterating through the class's MRO
    :return: An iterator yielding ``(method_name, method)`` tuples
    :raises TypeError: If ``cls`` is not a class
    """
    if not isinstance(cls, type):
        raise InvalidArgumentType("cls", cls, type)

    for name, method in iter_class_attributes(
        cls, start=start, start_after=start_after, bound=bound
    ):
        if name in DUNDERMETHOD_NAMES:
            yield name, method


def collect_class_dundermethods(
    cls: type,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> Dict[str, Any]:
    """
    Generates a dict of the form ``{method_name: method}`` containing all
    dundermethods implemented by the given class.

    If multiple classes in the MRO implement the same dundermethod, only the
    first implementation is included in the result.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param cls: The class whose dundermethods to collect
    :param start: Where to start iterating through the class's MRO
    :param start_after: Where to start iterating through the class's MRO
    :param bound: Where to stop iterating through the class's MRO
    :return: A ``{method_name: method}`` dict
    :raises TypeError: If ``cls`` is not a class
    """
    methods = {}

    for name, method in iter_class_dundermethods(
        cls, start=start, start_after=start_after, bound=bound
    ):
        methods.setdefault(name, method)

    return methods


def class_implements_dundermethod(
    cls: type,
    method_name: str,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> bool:
    """
    Checks whether the given class implements a certain dundermethod.

    The method is considered implemented if any of the classes in the MRO have
    an entry for ``method_name`` in their ``__dict__``. The only exceptions are
    methods from :attr:`NONEABLE_DUNDERMETHOD_NAMES`, which are considered *not*
    implemented if their value is ``None``.

    Note that :class:`object` implements various dundermethods, including some
    unexpected ones like ``__lt__``. Remember to pass in ``bound=object`` if you
    wish to exclude these.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param cls: A class
    :param method_name: The name of a dundermethod
    :param start: Where to start searching through the class's MRO
    :param start_after: Where to start searching through the class's MRO
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements that dundermethod
    :raises TypeError: If ``cls`` is not a class
    """
    for name, method in iter_class_attributes(
        cls, start=start, start_after=start_after, bound=bound
    ):
        if name == method_name:
            return _is_implemented(name, method)

    return False


def class_implements_dundermethods(
    cls: type,
    methods: Iterable[str],
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> bool:
    """
    Checks whether the given class implements all given dundermethods.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param cls: A class
    :param methods: The names of a bunch of dundermethods
    :param start: Where to start searching through the class's MRO
    :param start_after: Where to start searching through the class's MRO
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements all those dundermethods
    :raises TypeError: If ``cls`` is not a class
    """
    methods = set(methods)

    for name, method in iter_class_attributes(
        cls, start=start, start_after=start_after, bound=bound
    ):
        if name not in methods:
            continue

        if not _is_implemented(name, method):
            return False

        methods.remove(name)

    return not methods


def class_implements_any_dundermethod(
    cls: type,
    methods: Iterable[str],
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> bool:
    """
    Checks whether the given class implements at least one of the given
    dundermethods.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param cls: A class
    :param methods: The names of a bunch of dundermethods
    :param start: Where to start searching through the class's MRO
    :param start_after: Where to start searching through the class's MRO
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements any of those dundermethods
    :raises TypeError: If ``cls`` is not a class
    """
    methods = set(methods)
    seen = set()

    for name, method in iter_class_attributes(
        cls, start=start, start_after=start_after, bound=bound
    ):
        if name not in methods:
            continue

        if name in seen:
            continue
        seen.add(name)

        if not _is_implemented(name, method):
            continue

        return True

    return False


def get_class_dundermethod(
    cls: type,
    method_name: str,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> Optional[Callable]:
    """
    Retrieves a class's implementation of the given dundermethod.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param cls: A class
    :param method_name: The name of a dundermethod
    :param start: Where to start searching through the class's MRO
    :param start_after: Where to start searching through the class's MRO
    :param bound: Where to stop searching through the class's MRO
    :return: The function object for the given ``method_name``
    :raises TypeError: If ``cls`` is not a class
    :raises AttributeError: If ``cls`` does not implement that dundermethod
    """
    for name, method in iter_class_attributes(
        cls, start=start, start_after=start_after, bound=bound
    ):
        if name == method_name:
            return method

    raise DundermethodNotFound(method_name, cls)


def get_bound_dundermethod(
    instance: object,
    method_name: str,
    *,
    start: Optional[type] = None,
    start_after: Optional[type] = None,
    bound: Optional[type] = None,
) -> Optional[Callable]:
    """
    Retrieves an instance's implementation of the given dundermethod.

    Some dundermethods (for example ``__hash__``) can be explicitly disabled by
    setting them to ``None``. In such a case, this function will throw an
    ``AttributeError``.

    For details about ``start``, ``start_after`` and ``bound``, see
    :func:`~introspection.iter_class_dundermethods`.

    .. versionadded:: 1.1
    .. versionadded:: 1.4
        The ``start`` and ``start_after`` parameters.

    :param instance: Any object
    :param method_name: The name of a dundermethod
    :param start: Where to start searching through the class's MRO
    :param start_after: Where to start searching through the class's MRO
    :param bound: Where to stop searching through the class's MRO
    :return: A bound method for the given ``method_name``
    :raises DundermethodNotFound: If ``instance`` does not implement that dundermethod
    """
    cls = type(instance)
    error = DundermethodNotFound(method_name, cls)

    # Optimization: We can let `super` do most of the work for us. However, if
    # the dundermethod is none-able (like __hash__), then we have to avoid
    # `super` because we won't be able to tell if the method was set to None or
    # if it was a descriptor that returned None.
    if (
        method_name in NONEABLE_DUNDERMETHOD_NAMES
        or start is not None
        or start_after is not None
        or bound is not None
    ):
        # Manually extract it from the MRO
        dunder = get_class_dundermethod(
            cls,
            method_name,
            start=start,
            start_after=start_after,
            bound=bound,
        )
    else:
        # `super` fast track: Check if the method is implemented in the class,
        # and if not, use `super` to find it
        cls_vars = static_vars(cls)

        if method_name in cls_vars:
            dunder = cls_vars[method_name]
        else:
            proxy = super(cls, instance)

            try:
                return getattr(proxy, method_name)
            except AttributeError:
                raise error from None

    # At this point, we have retrieved the dunder from the class namespace
    if dunder is None and method_name in NONEABLE_DUNDERMETHOD_NAMES:
        raise error

    # If it's a descriptor, call its __get__ method.
    dunder_cls = type(dunder)

    # Optimization: If it's a built-in type, we can directly access its __get__
    # method without having to worry about any shenanigans
    if dunder_cls in (types.FunctionType, classmethod, staticmethod):
        return dunder.__get__(instance, cls)  # type: ignore

    # Even though __get__ is also a dundermethod, calling it here doesn't use
    # the usual mechanism for dundermethods. We simply get the `__get__`
    # attribute from the class and call it. That's it.
    try:
        get = get_class_dundermethod(dunder_cls, "__get__")
    except AttributeError:
        return dunder  # type: ignore

    return get(dunder, instance, cls)  # type: ignore


def call_dundermethod(
    instance: Any,
    method_name: str,
    *args,
    **kwargs,
) -> object:
    """
    Given an instance and the name of a dundermethod, calls the object's
    corresponding dundermethod. Excess arguments are passed to the dundermethod.

    Examples::

        >>> call_dundermethod('foo', '__len__')
        3
        >>> call_dundermethod([1], '__add__', [2])
        [1, 2]

    Alternatively, you can use the functions in the
    :mod:`introspection.dunder` module::

        >>> introspection.dunder.__len__('foo')
        3
        >>> introspection.dunder.add([1], [2])
        [1, 2]

    .. versionadded:: 1.4
    """
    method = get_bound_dundermethod(instance, method_name)
    return method(*args, **kwargs)  # type: ignore


import builtins
import copy
import types

from collections import defaultdict, deque
from typing import TypeVar, Any, Optional, Callable, Type, Dict, Iterable

__all__ = ['common_ancestor', 'create_class', 'resolve_bases', 'static_vars', 'static_copy']

T = TypeVar('T')


def create_class(name: str,
                 bases: Iterable = (),
                 attrs: dict = {},
                 metaclass: Optional[Callable[..., Type[T]]] = None,
                 **kwargs: Any
                 ) -> Type[T]:
    """
    Creates a new class. This is similar to :func:`types.new_class`,
    except it calls :func:`resolve_bases` even in python versions
    <= 3.7. (And it has a different interface.)

    :param name: The name of the new class
    :param bases: An iterable of bases classes
    :param attrs: A dict of class attributes
    :param metaclass: The metaclass, or ``None``
    :param kwargs: Keyword arguments to pass to the metaclass
    """
    if metaclass is not None:
        kwargs.setdefault('metaclass', metaclass)

    resolved_bases = resolve_bases(bases)
    meta, ns, kwds = types.prepare_class(name, resolved_bases, kwargs)

    ns.update(attrs)

    # Note: In types.new_class this is "is not" rather than "!="
    if resolved_bases != bases:
        ns['__orig_bases__'] = bases

    return meta(name, resolved_bases, ns, **kwds)


def resolve_bases(bases: Iterable) -> tuple:
    """
    Clone/backport of :func:`types.resolve_bases`.
    """
    result = []

    for base in bases:
        if isinstance(base, type):
            result.append(base)
            continue

        try:
            mro_entries = base.__mro_entries__
        except AttributeError:
            result.append(base)
            continue

        new_bases = mro_entries(bases)
        result.extend(new_bases)

    return tuple(result)


def static_vars(obj: Any):
    """
    Like :func:`vars`, but bypasses overridden ``__getattribute__`` methods.

    :param obj: Any object
    :return: The object's ``__dict__``
    :raises TypeError: If the object has no ``__dict__``
    """
    try:
        return object.__getattribute__(obj, '__dict__')
    except AttributeError:
        raise TypeError("{!r} object has no __dict__".format(obj)) from None


def static_copy(obj: Any):
    """
    Creates a copy of the given object without invoking any of its methods -
    ``__new__``, ``__init__``, ``__copy__`` or anything else.

    How it works:

    1. A new instance of the same class is created by calling
       ``object.__new__(type(obj))``.
    2. If ``obj`` has a ``__dict__``, the new instance's
       ``__dict__`` is updated with its contents.
    3. All values stored in ``__slots__`` (except for ``__dict__``
       and ``__weakref__``) are assigned to the new object.

    An exception are instances of builtin classes - these are copied
    by calling :func:`copy.copy`.

    .. versionadded: 1.1
    """
    from .classes import iter_slots

    cls = type(obj)

    # We'll check the __module__ attribute for speed and then also
    # make sure the class isn't lying about its module
    if cls.__module__ == 'builtins' and cls in vars(builtins).values():
        return copy.copy(obj)

    new_obj = object.__new__(cls)

    try:
        old_dict = static_vars(obj)
    except TypeError:
        pass
    else:
        static_vars(new_obj).update(old_dict)

    for slot_name, slot in iter_slots(cls):
        if slot_name in {'__dict__', '__weakref__'}:
            continue

        try:
            value = slot.__get__(obj, cls)
        except AttributeError:
            pass
        else:
            slot.__set__(new_obj, value)

    return new_obj


def common_ancestor(classes: Iterable[type]):
    """
    Finds the closest common parent class of the given classes.
    If called with an empty iterable, :class:`object` is returned.

    :param classes: An iterable of classes
    :return: The given classes' shared parent class
    """

    # How this works:
    # We loop through all classes' MROs, popping off the left-
    # most class from each. We keep track of how many MROs
    # that class appeared in. If it appeared in all MROs,
    # we return it.

    mros = [deque(cls.__mro__) for cls in classes]
    num_classes = len(mros)
    share_count = defaultdict(int)

    while mros:
        # loop through the MROs
        for mro in mros:
            # pop off the leftmost class
            cls = mro.popleft()
            share_count[cls] += 1

            # if it appeared in every MRO, return it
            if share_count[cls] == num_classes:
                return cls

        # remove empty MROs
        mros = [mro for mro in mros if mro]

    return object

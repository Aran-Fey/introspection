
from collections import defaultdict, deque
from typing import Any, Iterable

__all__ = ['common_ancestor', 'resolve_bases', 'static_vars']


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

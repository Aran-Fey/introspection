import weakref
import typing as t

from .misc import iter_wrapped


__all__ = ["does_not_alter_signature", "forwards_arguments"]


C = t.TypeVar("C", bound=t.Callable)


MARKS = weakref.WeakKeyDictionary[t.Callable, t.MutableSet[t.Callable]]()


def does_not_alter_signature(func: C) -> C:
    MARKS.setdefault(func, set()).add(does_not_alter_signature)
    return func


def forwards_arguments(func: C) -> C:
    MARKS.setdefault(func, set()).add(forwards_arguments)
    return func


def has_mark(func: t.Callable, mark: t.Callable) -> bool:
    for func in iter_wrapped(func):
        if mark in MARKS.get(func, ()):
            return True

    return False

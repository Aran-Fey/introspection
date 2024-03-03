import weakref
from typing import Callable, MutableSet, TypeVar


__all__ = ["does_not_alter_signature", "forwards_arguments"]


C = TypeVar("C", bound=Callable)


DOES_NOT_ALTER_SIGNATURE: MutableSet[Callable] = weakref.WeakSet()
FORWARDS_ARGUMENTS: MutableSet[Callable] = weakref.WeakSet()


def does_not_alter_signature(func: C) -> C:
    DOES_NOT_ALTER_SIGNATURE.add(func)
    return func


def forwards_arguments(func: C) -> C:
    FORWARDS_ARGUMENTS.add(func)
    return func

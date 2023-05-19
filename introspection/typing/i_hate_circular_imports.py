
import typing

from ..types import Type_, ParameterizedGeneric

__all__ = ['parameterize']


def parameterize(type_: Type_, args: typing.Iterable) -> ParameterizedGeneric:
    """
    .. versionadded: 1.6
    """
    args = tuple(args)

    if len(args) == 1:
        args = args[0]
    
    return type_[args]

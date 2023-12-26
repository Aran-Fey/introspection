import typing

from ..types import Type_, ParameterizedGeneric

__all__ = ["parameterize"]


def parameterize(
    type_: Type_,
    args: typing.Iterable[object],
) -> ParameterizedGeneric:
    """
    .. versionadded: 1.6
    """
    args = tuple(args)

    if len(args) == 1:
        return type_[args[0]]  # type: ignore

    return type_[args]  # type: ignore


from typing import List, Callable

from .parameter import Parameter
from .signature import Signature


__all__ = ['get_parameters']


def get_parameters(callable: Callable) -> List[Parameter]:
    """
    Returns a list of parameters accepted by *callable*.

    :param callable: the callable whose parameters to retrieve
    :return: a list of :class:`Parameter` instances
    """
    return list(Signature.from_callable(callable).parameters.values())

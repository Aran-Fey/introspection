
from typing import List, Callable

from .parameter import Parameter
from .signature import Signature


__all__ = ['get_parameters']


def get_parameters(callable_: Callable) -> List[Parameter]:
    """
    Returns a list of parameters accepted by *callable_*.

    :param callable_: The callable whose parameters to retrieve
    :return: A list of :class:`Parameter` instances
    """
    return list(Signature.from_callable(callable_).parameters.values())

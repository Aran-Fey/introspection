
from typing import Callable, List

from .signature import Signature
from .parameter import Parameter

__all__ = ['signature', 'get_parameters']


def signature(*args, **kwargs):
    """
    Shorthand for :meth:`Signature.from_callable`.
    """
    return Signature.from_callable(*args, **kwargs)


def get_parameters(callable_: Callable) -> List[Parameter]:
    """
    Returns a list of parameters accepted by ``callable_``.

    :param callable_: The callable whose parameters to retrieve
    :return: A list of :class:`Parameter` instances
    """
    return list(Signature.from_callable(callable_).parameters.values())

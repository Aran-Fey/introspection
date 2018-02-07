
import inspect
import functools
from typing import Union, List, Dict, Callable

from .Parameter import Parameter
from .introspection import get_parameters


class Signature(inspect.Signature):
    """
    Represents a function's parameter signature and return annotation.

    Implements the same interface as the :class:`inspect.Signature` class.

    :ivar parameters: an :class:`OrderedDict` of parameter names mapped to :class:`Parameter` instances
    :ivar return_annotation: the annotation for the return value, or *Signature.empty*
    """

    empty = inspect.Signature.empty

    def __init__(self,
                 parameters: Union[List[Parameter], Dict[str, Parameter], None] = None,
                 return_annotation: object = empty):  # FIXME: figure out why sphinx-autodoc messes up these default values
        super().__init__(parameters, return_annotation=return_annotation, __validate_parameters__=False)

    @classmethod
    def from_signature(cls, signature: inspect.Signature) -> 'Signature':
        """
        Creates a new `Signature` instance from an :class:`inspect.Signature` instance.

        :param signature: an :class:`inspect.Signature` instance
        :return: a new `Signature` instance
        """
        return cls(signature.parameters.values(), return_annotation=signature.return_annotation)

    @classmethod
    @functools.lru_cache()
    def from_callable(cls, callable: Callable) -> 'Signature':
        """
        Returns a matching :class:`Signature` instance for the given *callable*.

        :param callable: a function or any other callable object
        :return: a corresponding :class:`Signature` instance
        """

        parameters = get_parameters(callable)

        if isinstance(callable, type):
            return_annotation = callable
        else:
            try:
                sig = inspect.signature(callable)
            except ValueError:
                return_annotation = inspect.Signature.empty
            else:
                return_annotation = sig.return_annotation

        return cls(parameters, return_annotation=return_annotation)

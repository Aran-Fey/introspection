
import inspect
import functools

import datatypes

from .Parameter import Parameter
from .introspection import get_parameters


class Signature:
    def __init__(self, parameters, return_type=None):
        self.parameters = parameters
        self.return_type = return_type

    @classmethod
    def from_signature(cls, signature):
        parameters = [Parameter.from_parameter(param) for param in signature.parameters.values()]
        return_type = signature.annotation if isinstance(signature.annotation, (type, datatypes.Type)) else None
        return cls(parameters, return_type)

    @classmethod
    @functools.lru_cache()
    def from_callable(cls, callable):
        parameters = get_parameters(callable)

        if isinstance(callable, type):
            return_type = callable
        else:
            return_type = None
            try:
                sig = inspect.signature(callable)
            except ValueError:
                pass
            else:
                if isinstance(sig.annotation, (type, datatypes.Type)):
                    return_type = sig.annotation

        return cls(parameters, return_type)

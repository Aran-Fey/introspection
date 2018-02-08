
import re
import ast
import inspect

from typing import List, Callable

from .Parameter import Parameter
from .misc import *


__all__ = ['get_parameters']


def get_parameters(callable: Callable) -> List[Parameter]:
    """
    Returns a list of parameters accepted by *callable*.

    :param cls: the function or callable whose parameters to retrieve
    :return: a list of :class:`Parameter` instances
    """
    parameters = []

    try:
        sig = inspect.signature(callable)
    except ValueError:  # builtin types don't have an accessible signature
        # extract the parameter names and default values from the docstring
        doc = callable.__doc__
        pattern = re.compile(r'{}\((.*)\) -> '.format(callable.__name__))
        param_pattern = re.compile(r'(?P<name>\w+)(?:=(?P<default>[^,[)]+))?')

        for line in doc.splitlines():
            match = pattern.match(line)
            if not match:
                break

            paramlist = match.group(1)
            for i, match in enumerate(param_pattern.finditer(paramlist)):
                try:
                    param = parameters[i]
                except IndexError:
                    param = Parameter()
                    parameters.append(param)

                # many builtins accept a variable number of arguments, and
                # the different signatures are usually listed with an ascending
                # number of parameters.
                # Thanks to that, we can simply overwrite the parameter's attributes
                # and expect them to be correct in the end
                param.name = match.group('name')

                default = match.group('default')
                if default:
                    param.default = ast.literal_eval(default)

                    annotation = type(param.default)
                    if param.annotation != Parameter.empty:
                        annotation = common_ancestor(annotation, param.annotation)
                    param.annotation = annotation
    else:
        for parameter in sig.parameters.values():
            param = Parameter.from_parameter(parameter)
            parameters.append(param)

    return parameters

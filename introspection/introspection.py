
import re
import ast
import inspect
import functools

from typing import Dict, Any, Type, List, Callable, Iterable

from .Parameter import Parameter
from .utils import *

__all__ = ['get_attributes', 'get_configurable_attributes', 'get_constructor_parameters', 'get_parameters']


def get_attributes(obj: Any) -> Dict[str, Any]:
    """
    Returns a dictionary of all of *obj*'s attributes.

    :param obj: the object whose attributes will be returned
    :return: a dict of :code:`{attr_name: attr_value}`
    """
    return {attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}


# @functools.lru_cache()
def get_configurable_attributes(cls: type) -> Iterable[str]:
    """
    Returns a collection of all of *configurable* attributes of *cls* instances.

    An attribute is considered configurable if any of the following conditions apply:

     - It's a descriptor with a :code:`__set__` method
     - The class's constructor accepts a parameter with the same name

    :param cls: the class whose attributes will be returned
    :return: an iterable of attribute names
    """

    params = get_constructor_parameters(cls)
    attrs = {param.name for param in params}

    # iterate through all the class's descriptors and find those with a __set__ method
    for attr, value in get_attributes(cls).items():
        if hasattr(value, '__get__'):
            if not hasattr(value, '__set__') or (isinstance(value, property) and value.fset is None):
                pass
            else:
                attrs.add(attr)

    return attrs


def get_constructor_parameters(cls: type) -> List[Parameter]:
    """
    Returns a list of parameters accepted by *cls*'s constructor.

    :param cls: The class whose constructor parameters to retrieve
    :return: a list of :class:`Parameter` instances
    """
    return get_parameters(cls)


# @functools.lru_cache()
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
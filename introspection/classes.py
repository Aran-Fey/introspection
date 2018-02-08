
from typing import Dict, Any, List, Iterable

from .Parameter import Parameter
from .callables import *


__all__ = ['get_attributes', 'get_configurable_attributes', 'get_constructor_parameters']


def get_attributes(obj: Any) -> Dict[str, Any]:
    """
    Returns a dictionary of all of *obj*'s attributes.

    :param obj: the object whose attributes will be returned
    :return: a dict of :code:`{attr_name: attr_value}`
    """
    return {attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}


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



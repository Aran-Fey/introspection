
import inspect

from typing import Dict, Any, Iterable, Set

from .signature import Signature

__all__ = ['get_subclasses', 'get_attributes', 'get_configurable_attributes']


def get_subclasses(cls: type, include_abstract: bool = False) -> Set[type]:
    subclasses = set()
    queue = cls.__subclasses__()

    while queue:
        cls = queue.pop()

        if include_abstract or not inspect.isabstract(cls):
            subclasses.add(cls)

        queue += cls.__subclasses__()

    return subclasses


def get_attributes(obj: Any) -> Dict[str, Any]:
    """
    Returns a dictionary of all of ``obj``'s attributes.

    :param obj: The object whose attributes will be returned
    :return: A dict of :code:`{attr_name: attr_value}`
    """
    return {attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}


def get_configurable_attributes(cls: type) -> Iterable[str]:
    """
    Returns a collection of all of *configurable* attributes of *cls* instances.

    An attribute is considered configurable if any of the following conditions apply:

    * It's a descriptor with a :code:`__set__` method
    * The class's constructor accepts a parameter with the same name

    :param cls: The class whose attributes will be returned
    :return: An iterable of attribute names
    """

    params = Signature.from_class(cls).parameters.values()
    attrs = {param.name for param in params}

    # iterate through all the class's descriptors and find those with a __set__ method
    for attr, value in get_attributes(cls).items():
        if hasattr(value, '__get__'):
            if not hasattr(value, '__set__') or (isinstance(value, property) and value.fset is None):
                pass
            else:
                attrs.add(attr)

    return attrs


import collections
import inspect

from typing import Dict, Any, Set, Iterator

from .misc import static_vars

__all__ = ['get_subclasses', 'get_attributes',
           'iter_slots', 'get_slot_names', 'get_slots']


def get_subclasses(cls: type, include_abstract: bool = False) -> Set[type]:
    """
    Collects all subclasses of the given class.

    :param cls: A base class
    :param include_abstract: Whether abstract base classes should be included
    :return: A set of all subclasses
    """
    subclasses = set()
    queue = cls.__subclasses__()

    while queue:
        cls = queue.pop()

        if include_abstract or not inspect.isabstract(cls):
            subclasses.add(cls)

        queue += cls.__subclasses__()

    return subclasses


def iter_slots(cls: type) -> Iterator:
    for cls in cls.__mro__:  # pragma: no branch
        cls_vars = static_vars(cls)

        try:
            slots = cls_vars['__slots__']
        except KeyError:
            if cls.__module__ == 'builtins':
                break

            slots = (
                slot for slot in ('__weakref__', '__dict__')
                if slot in cls_vars
            )
        else:
            if isinstance(slots, str):
                slots = (slots,)

        for slot_name in slots:
            slot = cls_vars[slot_name]

            yield slot_name, slot


def get_slot_names(cls: type) -> Dict[str, int]:
    """
    Collects all of the given class's ``__slots__``, returning a
    dict of the form ``{slot_name: count}``.

    :param cls: The class whose slots to collect
    :return: A :class:`collections.Counter` counting the number of occurrences of each slot
    """
    slot_names = (name for name, _ in iter_slots(cls))
    return collections.Counter(slot_names)


def get_slots(cls: type) -> Dict[str, Any]:
    """
    Collects all of the given class's ``__slots__``, returning a
    dict of the form ``{slot_name: slot_descriptor}``.

    :param cls: The class whose slots to collect
    :return: A dict mapping slot names to descriptors
    """
    slots_dict = {}

    for slot_name, slot in iter_slots(cls):
        slots_dict.setdefault(slot_name, slot)

    return slots_dict


def get_attributes(obj: Any, include_weakref: bool = False) -> Dict[str, Any]:
    """
    Returns a dictionary of all of ``obj``'s attributes.

    :param obj: The object whose attributes will be returned
    :param include_weakref: Whether the ``__weakref__`` slot should be included in the result
    :return: A dict of ``{attr_name: attr_value}``
    """
    cls = type(obj)
    slots = get_slots(cls)

    slots.pop('__dict__', None)

    if not include_weakref:
        slots.pop('__weakref__', None)

    attrs = {name: slot.__get__(obj, cls) for name, slot in slots.items()}

    try:
        dict_ = static_vars(obj)
    except TypeError:
        pass
    else:
        attrs.update(dict_)

    return attrs

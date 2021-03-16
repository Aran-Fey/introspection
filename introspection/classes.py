
import collections
import inspect

from typing import Dict, Any, Set, Iterator, Tuple

from .misc import static_vars

__all__ = ['get_subclasses', 'get_attributes', 'safe_is_subclass',
           'iter_slots', 'get_slot_names', 'get_slot_counts', 'get_slots']


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


def iter_slots(cls: type) -> Iterator[Tuple[str, Any]]:
    """
    Iterates over all ``__slots__`` of the given class, yielding
    ``(slot_name, slot_descriptor)`` tuples.

    If a slot name is used more than once, *all* of them will be
    yielded in the order they appear in the class's MRO.

    Note that this function relies on the class-level ``__slots__``
    attribute - deleting or altering this attribute in any way may
    yield incorrect results.

    :param cls: The class whose slots to yield
    :return: An iterator yielding ``(slot_name, slot_descriptor)`` tuples
    """
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
            # apply name mangling if necessary
            if slot_name.startswith('__') and not slot_name.endswith('__'):
                slot_name = '_{}{}'.format(cls.__name__, slot_name)

            slot = cls_vars[slot_name]

            yield slot_name, slot


def get_slot_counts(cls: type) -> Dict[str, int]:
    """
    Collects all of the given class's ``__slots__``, returning a
    dict of the form ``{slot_name: count}``.

    :param cls: The class whose slots to collect
    :return: A :class:`collections.Counter` counting the number of occurrences of each slot
    """
    slot_names = (name for name, _ in iter_slots(cls))
    return collections.Counter(slot_names)


def get_slot_names(cls: type) -> Set[str]:
    """
    Collects all of the given class's ``__slots__``, returning a
    set of slot names.

    :param cls: The class whose slots to collect
    :return: A set containing the names of all slots
    """
    return set(get_slot_counts(cls))


def get_slots(cls: type) -> Dict[str, Any]:
    """
    Collects all of the given class's ``__slots__``, returning a
    dict of the form ``{slot_name: slot_descriptor}``.

    If a slot name is used more than once, only the descriptor
    that shadows all other descriptors of the same name is returned.

    :param cls: The class whose slots to collect
    :return: A dict mapping slot names to descriptors
    """
    slots_dict = {}

    for slot_name, slot in iter_slots(cls):
        slots_dict.setdefault(slot_name, slot)

    return slots_dict


def get_attributes(obj: Any, include_weakref: bool = False) -> Dict[str, Any]:
    """
    Returns a dictionary of all of ``obj``'s attributes. This includes
    attributes stored in the object's ``__dict__`` as well as in ``__slots__``.

    :param obj: The object whose attributes will be returned
    :param include_weakref: Whether the value of the ``__weakref__`` slot should be included in the result
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


def safe_is_subclass(subclass, superclass):
    """
    A clone of :func:`issubclass` that returns ``False`` instead of throwing a :exc:`TypeError`.
    
    .. versionadded:: 1.2
    """
    try:
        return issubclass(subclass, superclass)
    except TypeError:
        return False

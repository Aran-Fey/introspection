import collections
import inspect
import functools
from typing import *
from typing_extensions import *

import sentinel

from .mark import FORWARDS_ARGUMENTS, forwards_arguments
from .misc import static_vars, is_abstract, static_mro
from .errors import *
from .types import Slot, Function, Class

__all__ = [
    "iter_subclasses",
    "get_subclasses",
    "get_attributes",
    "get_abstract_method_names",
    "safe_is_subclass",
    "iter_slots",
    "get_slot_names",
    "get_slot_counts",
    "get_slots",
    "get_implicit_method_type",
    "fit_to_class",
    "add_method_to_class",
    "wrap_method",
]


T = TypeVar("T")

auto = sentinel.create("auto")


def iter_subclasses(cls: Type[T], include_abstract: bool = False) -> Iterator[Type[T]]:
    """
    Yields subclasses of the given class.

    .. versionadded:: 1.5

    :param cls: A base class
    :param include_abstract: Whether abstract base classes should be included
    :return: An iterator yielding subclasses
    """
    seen: Set[type] = set()
    queue: List[type] = cls.__subclasses__()

    while queue:
        subcls = queue.pop()

        if subcls in seen:
            continue
        seen.add(subcls)

        if include_abstract or not inspect.isabstract(subcls):
            yield subcls

        queue += subcls.__subclasses__()


def get_subclasses(cls: Type[T], include_abstract: bool = False) -> Set[Type[T]]:
    """
    Collects all subclasses of the given class.

    :param cls: A base class
    :param include_abstract: Whether abstract base classes should be included
    :return: A set of all subclasses
    """
    return set(iter_subclasses(cls, include_abstract=include_abstract))


def iter_slots(cls: type) -> Iterator[Tuple[str, Any]]:
    """
    Iterates over all ``__slots__`` of the given class, yielding
    ``(slot_name, slot_descriptor)`` tuples.

    If a slot name is used more than once, *all* of them will be yielded in the
    order they appear in the class's MRO.

    Note that this function relies on the class-level ``__slots__`` attribute -
    deleting or altering this attribute in any way may yield incorrect results.

    :param cls: The class whose slots to yield
    :return: An iterator yielding ``(slot_name, slot_descriptor)`` tuples
    """
    for cls in static_mro(cls):  # pragma: no branch
        cls_vars = static_vars(cls)

        try:
            slots = cast(Iterable[str], cls_vars["__slots__"])
        except KeyError:
            if cls.__module__ == "builtins":
                break

            slots = (slot for slot in ("__weakref__", "__dict__") if slot in cls_vars)
        else:
            if isinstance(slots, str):
                slots = (slots,)

        for slot_name in slots:
            # apply name mangling if necessary
            if slot_name.startswith("__") and not slot_name.endswith("__"):
                slot_name = "_{}{}".format(cls.__name__, slot_name)

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


def get_slots(cls: type) -> Dict[str, Slot[object]]:
    """
    Collects all of the given class's ``__slots__``, returning a
    dict of the form ``{slot_name: slot_descriptor}``.

    If a slot name is used more than once, only the descriptor
    that shadows all other descriptors of the same name is returned.

    :param cls: The class whose slots to collect
    :return: A dict mapping slot names to descriptors
    """
    slots_dict: Dict[str, Slot[object]] = {}

    for slot_name, slot in iter_slots(cls):
        slots_dict.setdefault(slot_name, slot)

    return slots_dict


def get_attributes(obj: Any, include_weakref: bool = False) -> Dict[str, object]:
    """
    Returns a dictionary of all of ``obj``'s attributes. This includes
    attributes stored in the object's ``__dict__`` as well as in ``__slots__``.

    :param obj: The object whose attributes will be returned
    :param include_weakref: Whether the value of the ``__weakref__`` slot should
        be included in the result
    :return: A dict of ``{attr_name: attr_value}``
    """
    try:
        attrs = dict(static_vars(obj))
    except ObjectHasNoDict:
        attrs: Dict[str, object] = {}

    cls = type(obj)
    slots = get_slots(cls)

    slots.pop("__dict__", None)

    if not include_weakref:
        slots.pop("__weakref__", None)

    # TODO: Is this the correct way to invoke the descriptor's __get__?
    for name, slot in slots.items():
        try:
            attrs[name] = slot.__get__(obj, cls)
        except AttributeError:
            continue

    return attrs


def get_abstract_method_names(cls: type) -> Set[str]:
    """
    Returns a set of names of abstract methods (and other things) in the given
    class. See also :func:`~introspection.is_abstract`.

    .. versionadded:: 1.4

    :param cls: A class
    :return: The names of all abstract methods in that class
    """
    result: Set[str] = set()
    seen: Set[str] = set()

    for cls_ in static_mro(cls):
        for name, value in static_vars(cls_).items():
            if name in seen:
                continue
            seen.add(name)

            if is_abstract(value) and not isinstance(value, type):
                result.add(name)

    return result


def safe_is_subclass(subclass: object, superclass: Class) -> TypeGuard[Type[Class]]:
    """
    A clone of :func:`issubclass` that returns ``False`` instead of throwing a
    :exc:`TypeError`.

    .. versionadded:: 1.2

    :param subclass: The subclass
    :param superclass: The superclass
    :return: Whether ``subclass`` is a subclass of ``superclass``
    """
    try:
        return issubclass(subclass, superclass)  # type: ignore
    except TypeError:
        return False


def get_implicit_method_type(
    method_name: str,
) -> Union[None, Type[staticmethod], Type[classmethod]]:
    """
    Given the name of a method as input, returns what kind of method python automatically
    converts it to. The return value can be :class:`staticmethod`, :class:`classmethod`,
    or ``None``.

    Examples::

        >>> get_implicit_method_type('frobnicate_quadrizzles')
        >>> get_implicit_method_type('__new__')
        <class 'staticmethod'>
        >>> get_implicit_method_type('__init_subclass__')
        <class 'classmethod'>

    .. versionadded:: 1.3

    :param method_name: The name of a dundermethod
    :return: The type of that method
    """
    TYPES_BY_NAME: Dict[str, Any] = {
        "__new__": staticmethod,
        "__init_subclass__": classmethod,
        "__class_getitem__": classmethod,
    }

    return TYPES_BY_NAME.get(method_name)


def fit_to_class(
    thing: Union[type, Function],
    cls: type,
    name: Optional[str] = None,
) -> None:
    r"""
    Updates ``thing``\ 's metadata to match ``cls``\ 's.

    ``thing`` can be one of the following:

    - A function
    - A :any:`staticmethod`
    - A :any:`classmethod`
    - A :any:`property`

    If ``name`` is not ``None``, ``thing`` will be renamed accordingly.

    .. versionadded:: 1.4

    :param thing: The thing whose metadata should be updated
    :param cls: The class to copy the metadata from
    :param name: The name to rename ``thing`` to
    """
    methods: List[Union[type, Function]]

    if isinstance(thing, (classmethod, staticmethod)):
        methods = [thing.__func__]  # type: ignore
    elif isinstance(thing, property):
        methods = [method for method in (thing.fget, thing.fset, thing.fdel) if method is not None]  # type: ignore
    else:
        methods = [thing]

    for method in methods:
        if name is None:
            method_name = method.__name__
        else:
            method_name = name

        method.__name__ = method_name
        method.__qualname__ = cls.__qualname__ + "." + method_name
        method.__module__ = cls.__module__


def add_method_to_class(
    method: Callable[..., object],
    cls: type,
    name: Optional[str] = None,
    method_type: Union[None, Type[staticmethod], Type[classmethod]] = auto,  # type: ignore
) -> None:
    r"""
    Adds ``method`` to ``cls``\ 's namespace under the given ``name``.

    If ``name`` is ``None``, it defaults to ``method.__name__``.

    The method's metadata (``__name__``, ``__qualname__``, and ``__module__``)
    will be updated to match the class.

    If a ``method_type`` is passed in, it should have a value of :class:`staticmethod`,
    :class:`classmethod`, or ``None``. If omitted, it is automatically determined by
    calling :func:`~introspection.get_implicit_method_type`. The method is then automatically
    wrapped with the appropriate descriptor.

    .. versionadded:: 1.3

    :param method: The method to add to the class
    :param cls: The class to which to add the method
    :param name: The name under which the method is registered in the class namespace
    :param method_type: One of :class:`staticmethod`, :class:`classmethod`, or ``None`` (or omitted)
    """
    fit_to_class(method, cls, name)  # type: ignore
    method_name = method.__name__

    if method_type is auto:
        method_type = get_implicit_method_type(method_name)

    if method_type is not None:
        method = method_type(method)  # type: ignore

    setattr(cls, method_name, method)


def wrap_method(
    method: Callable[..., Any],
    cls: type,
    name: Optional[str] = None,
    method_type: Union[None, Type[staticmethod], Type[classmethod]] = auto,  # type: ignore
) -> None:
    r"""
    Adds ``method`` to ``cls``\ 's namespace under the given ``name``, wrapping the existing method
    (if one exists).

    The replaced method will be passed in as the first positional argument (even before the implicit
    ``self``). If the class previously didn't implement this method, an appropriate dummy method
    will be passed in instead, which merely sends the call further up the MRO.

    ``method_type`` has the same meaning as it does in :func:`~introspection.add_method_to_class`.

    Example::

        class Foo:
            def __init__(self, foo):
                self.foo = foo

            def __repr__(self):
                return f'<Foo object with foo={self.foo}>'

        def custom_init(original_init, self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            print('Initialized instance:', self)

        wrap_method(custom_init, Foo, '__init__')

        Foo(5)  # prints "Initialized instance: <Foo object with foo=5>"

    .. note::
        Adding a ``__new__`` method to a class can lead to unexpected problems because of the way
        ``object.__new__`` works.

        If a class doesn't implement a ``__new__`` method at all, ``object.__new__`` silently
        discards any arguments it receives. But if a class does implement a custom ``__new__``
        method, passing arguments into ``object.__new__`` will throw an exception::

            class ThisWorks:
                def __init__(self, some_arg):
                    pass

            class ThisDoesntWork:
                def __new__(cls, *args, **kwargs):
                    return super().__new__(cls, *args, **kwargs)

                def __init__(self, some_arg):
                    pass

            ThisWorks(5)  # works
            ThisDoesntWork(5)  # throws TypeError: object.__new__() takes exactly one argument

        This is why, when this function is used to add a ``__new__`` method to a class that
        previously didn't have one, it automatically generates a dummy ``__new__`` that *attempts*
        to figure out whether it should forward its arguments to the base class's ``__new__`` method
        or not. This is why the following code will work just fine::

            class ThisWorks:
                def __init__(self, some_arg):
                    pass

            def __new__(original_new, cls, *args, **kwargs):
                return original_new(cls, *args, **kwargs)

            wrap_method(__new__, ThisWorks)

            ThisWorks(5)  # works!

        However, it is impossible to always correctly figure out if the arguments should be passed
        on or not. If there is another ``__new__`` method that passes on its arguments, things will
        go wrong::

            class Parent:
                def __init__(self, some_arg):
                    pass

            class Child(Parent):
                def __new__(cls, *args, **kwargs):
                    return super().__new__(cls, *args, **kwargs)

            def __new__(original_new, cls, *args, **kwargs):
                return original_new(cls, *args, **kwargs)

            wrap_method(__new__, Parent)

            Parent(5)  # works!
            Child(5)  # throws TypeError

        In such a scenario, the method sees that ``Child.__new__`` exists, and therefore it is
        ``Child.__new__``\ 's responsibility to handle the arguments correctly. It should consume
        all the arguments, but doesn't, so an exception is raised.

        As a workaround, you can mark ``Child.__new__`` as a method that forwards its arguments.
        This is done by decorating it with ``@introspection.mark.forwards_arguments`::

            @introspection.mark.forwards_arguments
            def __new__(original_new, cls, *args, **kwargs):
                return original_new(cls, *args, **kwargs)

            wrap_method(__new__, Parent)

            Child(5)  # works!

    .. versionadded:: 1.3

    :param method: The method to add to the class
    :param cls: The class to which to add the method
    :param name: The name under which the method is registered in the class namespace
    :param method_type: One of :class:`staticmethod`, :class:`classmethod`, or ``None`` (or omitted)
    """
    if not isinstance(cls, type):
        raise InvalidArgumentType("cls", cls, type)

    if name is None:
        name = method.__name__

    if method_type is auto:
        method_type = get_implicit_method_type(name)

    original_method, wrap_original = _get_original_method(cls, name, method_type)

    @wrap_original
    def replacement_method(*args, **kwargs):
        return method(original_method, *args, **kwargs)

    add_method_to_class(replacement_method, cls, name, method_type=method_type)


def _get_original_method(cls: type, method_name: str, method_type):
    cls_vars = static_vars(cls)

    original_method: Callable[..., Any]

    try:
        original_method = cls_vars[method_name]  # type: ignore
    except KeyError:
        # === SPECIAL METHOD: __new__ ===
        if method_name == "__new__":
            original_method, wrap_original = _make_original_new_method(cls)

        # === STATICMETHODS ===
        elif method_type is staticmethod:

            def _original_method1(*args, **kwargs):
                super_method = getattr(super(cls, cls), method_name)  # type: ignore[wtf]
                return super_method(*args, **kwargs)

            original_method = _original_method1
            wrap_original = lambda func: func

        # === INSTANCE- AND CLASSMETHODS ===
        else:

            def _original_method2(self_or_cls, *args, **kwargs):
                super_method = getattr(super(cls, self_or_cls), method_name)  # type: ignore[wtf]
                return super_method(*args, **kwargs)

            original_method = _original_method2
            wrap_original = lambda func: func
    else:
        if isinstance(original_method, (staticmethod, classmethod)):
            original_method = original_method.__func__

        wrap_original = functools.wraps(original_method)

    return original_method, wrap_original


def _make_original_new_method(cls: type):
    def original_method(class_: type, *args, **kwargs):
        super_new = super(cls, class_).__new__  # type: ignore[wtf]

        # object.__new__ accepts no arguments if the class implements its own __new__ method, so we
        # must take care to not pass it any if this is the only __new__ method in the whole MRO. But
        # if there's no __init__ method either, then receiving any arguments should results in an
        # exception.

        # If super_new is not object.__new__, then it's their responsibility to deal with the
        # arguments. In this case, we always forward them. If the class implements no __init__
        # method at all, we forward them as well.
        if super_new is object.__new__ and class_.__init__ is not object.__init__:
            # At this point, we know that the next __new__ method in the MRO is object.__new__, so
            # we must decide how to handle the arguments.

            # If there's a __new__ method in the MRO that is not object.__new__ and is not marked as
            # `@forwards_arguments`, then that method should've consumed all the arguments.
            forward_args = False

            for c in static_mro(class_):  # pragma: no branch
                if c is object:
                    break

                try:
                    # __new__ is always wrapped in `staticmethod`
                    new = static_vars(c)["__new__"].__func__  # type: ignore
                except KeyError:
                    continue

                if new in FORWARDS_ARGUMENTS:
                    continue

                if getattr(new, "_forwards_args", False):  # Legacy version of `@forwards_arguments`
                    continue

                forward_args = True
                break

            if not forward_args:
                args = ()
                kwargs = {}

        return super_new(class_, *args, **kwargs)  # type: ignore

    # We're just gonna assume that the user is going to properly call our original_method, because
    # if not, they should've just used `add_method_to_class` instead.
    wrap_original = forwards_arguments

    return original_method, wrap_original

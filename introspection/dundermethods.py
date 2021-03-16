
from typing import Iterator, Iterable, Tuple, Dict, Any, Callable, Optional

from .misc import static_vars

__all__ = ['DUNDERMETHOD_NAMES', 'AUGMENTED_ASSIGNMENT_DUNDERMETHOD_NAMES',
           'iter_class_dundermethods', 'class_implements_dundermethod', 'class_implements_any_dundermethod', 'class_implements_dundermethods', 'collect_class_dundermethods', 'get_class_dundermethod',
           'get_bound_dundermethod']


# An incomplete(!) list of dundermethods can be found on the data model page:
# https://docs.python.org/3/reference/datamodel.html
#: A set containing the names of all dundermethods available in python 3.9.
DUNDERMETHOD_NAMES = {'__abs__', '__add__', '__aenter__', '__aexit__', '__aiter__', '__and__', '__anext__', '__await__', '__bool__', '__bytes__', '__call__', '__complex__', '__contains__', '__delattr__', '__delete__', '__delitem__', '__delslice__', '__dir__', '__div__', '__divmod__', '__enter__', '__eq__', '__exit__', '__float__', '__floordiv__', '__format__', '__fspath__', '__ge__', '__get__', '__getattribute__', '__getitem__', '__getnewargs__', '__getslice__', '__gt__', '__hash__', '__iadd__', '__iand__', '__imul__', '__index__', '__init__', '__init_subclass__', '__instancecheck__', '__int__', '__invert__', '__ior__', '__isub__', '__iter__', '__ixor__', '__le__', '__len__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', '__neg__', '__new__', '__next__', '__or__', '__pos__', '__pow__', '__prepare__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__', '__round__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__', '__rxor__', '__set__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__sub__', '__subclasscheck__', '__subclasses__', '__truediv__', '__xor__', '__rmatmul__', '__imatmul__', '__ifloordiv__', '__class_getitem__', '__irshift__', '__floor__', '__ilshift__', '__length_hint__', '__del__', '__matmul__', '__ipow__', '__getattr__', '__set_name__', '__ceil__', '__imod__', '__itruediv__', '__trunc__'}

#: A set containing the names of all augmented assignment dundermethods
#: available in python 3.9.
#:
#: .. versionadded:: 1.1
AUGMENTED_ASSIGNMENT_DUNDERMETHOD_NAMES = {
    '__iadd__',
    '__isub__',
    '__imul__',
    '__imatmul__',
    '__itruediv__',
    '__ifloordiv__',
    '__imod__',
    '__ipow__',
    '__ilshift__',
    '__irshift__',
    '__iand__',
    '__ixor__',
    '__ior__',
}


def _is_implemented(name, method):
    if name == '__hash__':
        return method is not None
    else:
        return True


def iter_class_dundermethods(cls: type,
                             bound: Optional[type] = None,
                             ) -> Iterator[Tuple[str, Any]]:
    """
    Yields all dundermethods implemented by the given class as
    ``(method_name, method)`` tuples.

    (For the purpose of this function, "implemented" simply
    means "exists". Even if the method's value is ``None`` or
    anything else, it will still be yielded.)

    If multiple classes in the MRO implement the same dundermethod,
    both methods will be yielded. Methods implemented by subclasses
    will always be yielded before methods implemented by parent
    classes.

    You can cause the iteration to stop early by passing in a class
    as the upper ``bound``. The MRO will only be iterated up to
    the ``bound``, excluding the ``bound`` class itself. This is
    useful for excluding dundermethods implemented in :class:`object`.

    :param cls: The class whose dundermethods to yield
    :param bound: Where to stop iterating through the class's MRO
    :return: An iterator yielding ``(method_name, method)`` tuples
    :raises TypeError: If ``cls`` is not a class
    """
    if not isinstance(cls, type):
        raise TypeError("'cls' argument must be a class, not {}".format(cls))

    for cl in cls.__mro__:
        if cl is bound:
            break

        cls_vars = static_vars(cl)

        for name, method in cls_vars.items():
            if name in DUNDERMETHOD_NAMES:
                yield name, method


def collect_class_dundermethods(cls: type,
                                bound: Optional[type] = None,
                                ) -> Dict[str, Any]:
    """
    Generates a dict of the form ``{method_name: method}``
    containing all dundermethods implemented by the given class.

    If multiple classes in the MRO implement the same dundermethod,
    only the first implementation is included in the result.

    :param cls: The class whose dundermethods to collect
    :param bound: Where to stop iterating through the class's MRO
    :return: A ``{method_name: method}`` dict
    :raises TypeError: If ``cls`` is not a class
    """
    methods = {}

    for name, method in iter_class_dundermethods(cls, bound=bound):
        methods.setdefault(name, method)

    return methods


def class_implements_dundermethod(cls: type,
                                  method_name: str,
                                  bound: Optional[type] = None,
                                  ) -> bool:
    """
    Checks whether the given class implements a certain dundermethod.

    The method is considered implemented if any of the classes in the
    MRO have an entry for ``method_name`` in their ``__dict__``. The
    only exception is that ``__hash__`` methods are considered *not*
    implemented if their value is ``None``.

    Note that :class:`object` implements various dundermethods,
    including some unexpected ones like ``__lt__``. Remember to pass
    in ``bound=object`` if you wish to exclude these.

    :param cls: A class
    :param method_name: The name of a dundermethod
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements that dundermethod
    :raises TypeError: If ``cls`` is not a class
    """
    for name, method in iter_class_dundermethods(cls, bound=bound):
        if name == method_name:
            return _is_implemented(name, method)

    return False


def class_implements_dundermethods(cls: type,
                                   methods: Iterable[str],
                                   bound: Optional[type] = None,
                                   ) -> bool:
    """
    Checks whether the given class implements all given dundermethods.

    :param cls: A class
    :param methods: The names of a bunch of dundermethods
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements all those dundermethods
    :raises TypeError: If ``cls`` is not a class
    """
    methods = set(methods)

    for name, method in iter_class_dundermethods(cls, bound=bound):
        if name not in methods:
            continue

        if not _is_implemented(name, method):
            return False

        methods.remove(name)

    return not methods


def class_implements_any_dundermethod(cls: type,
                                      methods: Iterable[str],
                                      bound: Optional[type] = None,
                                      ) -> bool:
    """
    Checks whether the given class implements at least one of the
    given dundermethods.

    :param cls: A class
    :param methods: The names of a bunch of dundermethods
    :param bound: Where to stop searching through the class's MRO
    :return: A boolean indicating whether the class implements any of those dundermethods
    :raises TypeError: If ``cls`` is not a class
    """
    methods = set(methods)
    seen = set()

    for name, method in iter_class_dundermethods(cls, bound=bound):
        if name not in methods:
            continue

        if name in seen:
            continue
        seen.add(name)

        if not _is_implemented(name, method):
            continue

        return True

    return False


def get_class_dundermethod(cls: type,
                           method_name: str,
                           bound: Optional[type] = None,
                           ) -> Optional[Callable]:
    """
    Retrieves a class's implementation of the given dundermethod.

    :param cls: A class
    :param method_name: The name of a dundermethod
    :param bound: Where to stop searching through the class's MRO
    :return: The function object for the given ``method_name``
    :raises TypeError: If ``cls`` is not a class
    :raises AttributeError: If ``cls`` does not implement that dundermethod
    """
    for name, method in iter_class_dundermethods(cls, bound=bound):
        if name == method_name:
            return method

    msg = "class {!r} does not implement {}"
    raise AttributeError(msg.format(cls, method_name))


def get_bound_dundermethod(instance: Any,
                           method_name: str,
                           bound: Optional[type] = None,
                           ) -> Optional[Callable]:
    """
    Retrieves an instance's implementation of the given dundermethod.

    .. versionadded:: 1.1

    :param instance: Any object
    :param method_name: The name of a dundermethod
    :param bound: Where to stop searching through the class's MRO
    :return: A bound method for the given ``method_name``
    :raises AttributeError: If ``instance`` does not implement that dundermethod
    """
    cls = type(instance)
    method = get_class_dundermethod(cls, method_name, bound)

    return method.__get__(instance, cls)

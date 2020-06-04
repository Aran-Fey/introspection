
from typing import Iterator, Iterable, Tuple, Dict, Any

from .misc import static_vars

__all__ = ['iter_class_dundermethods', 'class_implements_dundermethod', 'class_implements_any_dundermethod', 'class_implements_dundermethods', 'collect_class_dundermethods']


"""
An incomplete(!) list of dundermethods can be found on the data model page:

    https://docs.python.org/3/reference/datamodel.html
"""
DUNDERMETHODS = {'__abs__', '__add__', '__aenter__', '__aexit__', '__aiter__', '__and__', '__anext__', '__await__', '__bool__', '__bytes__', '__call__', '__complex__', '__contains__', '__delattr__', '__delete__', '__delitem__', '__delslice__', '__dir__', '__div__', '__divmod__', '__enter__', '__eq__', '__exit__', '__float__', '__floordiv__', '__format__', '__fspath__', '__ge__', '__get__', '__getattribute__', '__getitem__', '__getnewargs__', '__getslice__', '__gt__', '__hash__', '__iadd__', '__iand__', '__imul__', '__index__', '__init__', '__init_subclass__', '__instancecheck__', '__int__', '__invert__', '__ior__', '__isub__', '__iter__', '__ixor__', '__le__', '__len__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', '__neg__', '__new__', '__next__', '__or__', '__pos__', '__pow__', '__prepare__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__', '__round__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__', '__rxor__', '__set__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__sub__', '__subclasscheck__', '__subclasses__', '__truediv__', '__xor__', '__rmatmul__', '__imatmul__', '__ifloordiv__', '__class_getitem__', '__irshift__', '__floor__', '__ilshift__', '__length_hint__', '__del__', '__matmul__', '__ipow__', '__getattr__', '__set_name__', '__ceil__', '__imod__', '__itruediv__', '__trunc__'}


def _is_implemented(name, method):
    if name == '__hash__':
        return method is not None
    else:
        return True


def iter_class_dundermethods(cls: type) -> Iterator[Tuple[str, Any]]:
    if not isinstance(cls, type):
        raise TypeError("'cls' argument must be a class, not {}".format(cls))

    for cl in cls.__mro__:
        cls_vars = static_vars(cl)

        for name, method in cls_vars.items():
            if name in DUNDERMETHODS:
                yield name, method


def collect_class_dundermethods(cls: type) -> Dict[str, Any]:
    methods = {}

    for name, method in iter_class_dundermethods(cls):
        methods.setdefault(name, method)

    return methods


def class_implements_dundermethod(cls: type, method_name: str) -> bool:
    for name, method in iter_class_dundermethods(cls):
        if name == method_name:
            return _is_implemented(name, method)

    return False


def class_implements_dundermethods(cls: type, methods: Iterable[str]) -> bool:
    methods = set(methods)

    for name, method in iter_class_dundermethods(cls):
        if name not in methods:
            continue

        if not _is_implemented(name, method):
            return False

        methods.remove(name)

    return not methods


def class_implements_any_dundermethod(cls: type, methods: Iterable[str]) -> bool:
    methods = set(methods)

    for name, method in iter_class_dundermethods(cls):
        if name not in methods:
            continue

        if not _is_implemented(name, method):
            continue

        return True

    return False

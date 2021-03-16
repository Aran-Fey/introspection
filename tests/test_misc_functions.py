
import pytest

import abc
import typing

from introspection import *


def test_get_parameters():
    def func(a: int, b=True):
        pass

    sig = Signature.from_callable(func)
    assert get_parameters(func) == sig.parameter_list


def test_static_vars():
    class Foo:
        def __init__(self):
            self.x = 4

        def __getattribute__(self, item):
            raise ZeroDivisionError

    foo = Foo()
    attrs = static_vars(foo)
    assert attrs == {'x': 4}


def test_static_copy():
    class Foo:
        __slots__ = ['foo', '__dict__']

    foo = Foo()
    foo.foo = []

    foo_copy = static_copy(foo)

    assert type(foo_copy) is type(foo)
    assert foo_copy.foo is foo.foo
    assert 'bar'


def test_static_copy_empty_slot():
    class Foo:
        __slots__ = ['foo', 'bar']

    foo = Foo()
    foo.bar = 5

    foo_copy = static_copy(foo)

    assert foo_copy.bar == foo.bar


def test_static_copy_doesnt_transfer_descriptors():
    class Foo:
        @property
        def attr(self):
            return 5

    foo = Foo()
    foo_copy = static_copy(foo)

    assert 'attr' not in vars(foo_copy)


def test_static_copy_is_shallow():
    class Foo:
        pass

    foo = Foo()
    foo.bar = []

    foo_copy = static_copy(foo)

    assert foo_copy.bar is foo.bar


def test_static_copy_builtin():
    foo = [1, 2]
    foo_copy = static_copy(foo)

    assert foo_copy == foo
    assert foo_copy is not foo


@pytest.mark.parametrize('classes,ancestor', [
    ([], object),
    ([str], str),
    ([int, bool], int),
    ([bool, int], int),
    ([int, float], object),
    ([Exception, IndexError, LookupError], Exception),
])
def test_common_ancestor(classes, ancestor):
    anc = common_ancestor(classes)
    assert anc is ancestor


def test_resolve_bases():
    class Fake:
        def __init__(self, mro_entries):
            self.mro_entries = mro_entries

        def __mro_entries__(self, bases):
            return self.mro_entries

    bases = (Fake(()), Fake([list]), int, 5)

    assert resolve_bases(bases) == (list, int, 5)


@pytest.mark.parametrize('metaclass', [
    type,
    abc.ABCMeta,
])
def test_create_class(metaclass):
    cls = create_class(
        'MyClass',
        (typing.List,),
        {'x': 5},
        metaclass=metaclass,
    )

    assert cls.__name__ == 'MyClass'
    assert isinstance(cls, metaclass)
    assert issubclass(cls, list)
    assert cls.x == 5


def test_create_class_no_meta():
    class MROEntries:
        def __mro_entries__(self, bases):
            return (list,)

    cls = create_class(
        'MyClass',
        (MROEntries(),)
    )

    assert cls.__name__ == 'MyClass'
    assert type(cls) is type
    assert issubclass(cls, list)


def test_create_class_no_mro_entries():
    cls = create_class(
        'MyClass',
        (list,)
    )

    assert cls.__name__ == 'MyClass'
    assert type(cls) is type
    assert issubclass(cls, list)


import abc

from introspection.classes import *


def test_get_subclasses():
    class A: pass
    class B(A): pass
    class C(A): pass
    class D(B, C): pass

    assert get_subclasses(A) == {B, C, D}


def test_get_subclasses_with_abstract_classes():
    class A(abc.ABC):
        @abc.abstractmethod
        def foo(self): pass

    class B(A): pass
    class C(A): foo = vars
    class D(B, C): pass

    assert get_subclasses(A) == {C, D}


def test_get_subclasses_include_abstract():
    class A(abc.ABC):
        @abc.abstractmethod
        def foo(self): pass

    class B(A): pass
    class C(A): foo = vars
    class D(B, C): pass

    assert get_subclasses(A, include_abstract=True) == {B, C, D}


def test_get_slot_names_tuple():
    class Foo:
        __slots__ = ('foo', 'bar')

    assert get_slot_names(Foo) == {'foo': 1, 'bar': 1}


def test_get_slot_names_str():
    class Foo:
        __slots__ = 'foo'

    assert get_slot_names(Foo) == {'foo': 1}


def test_get_slot_names_inheritance():
    class Foo:
        __slots__ = 'foo'

    class Bar(Foo):
        __slots__ = ['foo', 'bar']

    assert get_slot_names(Bar) == {'foo': 2, 'bar': 1}


def test_get_slot_names_omitted():
    class Foo:
        pass

    assert get_slot_names(Foo) == {'__weakref__': 1, '__dict__': 1}

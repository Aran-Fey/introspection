
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


def test_get_slot_counts_tuple():
    class Foo:
        __slots__ = ('foo', 'bar')

    assert get_slot_counts(Foo) == {'foo': 1, 'bar': 1}


def test_get_slot_counts_str():
    class Foo:
        __slots__ = 'foo'

    assert get_slot_counts(Foo) == {'foo': 1}


def test_get_slot_counts_mangled():
    class Foo:
        __slots__ = ('__foo', '__bar__')

    assert get_slot_counts(Foo) == {'_Foo__foo': 1, '__bar__': 1}


def test_get_slot_counts_inheritance():
    class Foo:
        __slots__ = 'foo'

    class Bar(Foo):
        __slots__ = ['foo', 'bar']

    assert get_slot_counts(Bar) == {'foo': 2, 'bar': 1}


def test_get_slot_counts_omitted():
    class Foo:
        pass

    assert get_slot_counts(Foo) == {'__weakref__': 1, '__dict__': 1}


def test_get_slot_names():
    class Foo:
        __slots__ = 'foo'

    class Bar(Foo):
        __slots__ = ['foo', 'bar']

    assert get_slot_names(Bar) == {'foo', 'bar'}


def test_get_slots_inheritance():
    class Foo:
        __slots__ = 'foo'

    class Bar(Foo):
        __slots__ = ['foo', 'bar']

    class Baz(Bar):
        __slots__ = ('baz',)

    slots = get_slots(Baz)
    assert len(slots) == 3
    assert slots['foo'] is Baz.foo
    assert slots['bar'] is Baz.bar
    assert slots['baz'] is Baz.baz


def test_get_attributes_slots_and_dict():
    class Foo:
        __slots__ = 'foo'

    class Bar(Foo):
        pass

    obj = Bar()
    obj.foo = 3
    obj.bar = 5

    assert get_attributes(obj) == {'foo': 3, 'bar': 5}


def test_get_attributes_slots():
    class Foo:
        __slots__ = 'foo'

    obj = Foo()
    obj.foo = 3

    assert get_attributes(obj) == {'foo': 3}


def test_get_attributes_with_weakref():
    class Foo:
        pass

    obj = Foo()
    obj.foo = 3

    attrs = get_attributes(obj, include_weakref=True)
    assert attrs == {'foo': 3, '__weakref__': None}

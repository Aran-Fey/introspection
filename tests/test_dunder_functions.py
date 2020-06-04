
import pytest

from introspection import *


def test_collect_dundermethods():
    class Parent:
        def __setitem__(self, key, value):
            pass

    class Child(Parent):
        def __len__(self):
            return 3

    dunders = collect_class_dundermethods(Child)
    assert dunders['__len__'] is Child.__len__
    assert dunders['__setitem__'] is Parent.__setitem__
    assert '__reversed__' not in dunders


def test_class_implements_dundermethod():
    class Class:
        def __len__(self):
            pass

    assert class_implements_dundermethod(Class, '__len__')


def test_class_implements_dundermethod_handles_meta():
    class Meta(type):
        def __len__(self):
            pass

    class Class(metaclass=Meta):
        pass

    assert not class_implements_dundermethod(Class, '__len__')


def test_class_implements_dundermethod_with_nonclass():
    with pytest.raises(TypeError):
        class_implements_dundermethod(3, '__len__')

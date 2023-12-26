import pytest

from functools import partial

import introspection.dunder
from introspection import *


@pytest.mark.parametrize(
    "func",
    [
        lambda *args, **kwargs: list(iter_class_dundermethods(*args, **kwargs)),
        collect_class_dundermethods,
        partial(class_implements_dundermethod, method_name="__len__"),
        partial(class_implements_dundermethods, methods=["__len__"]),
        partial(class_implements_any_dundermethod, methods=["__len__"]),
        partial(get_class_dundermethod, method_name="__len__"),
        partial(get_bound_dundermethod, method_name="__len__"),
    ],
)
def test_conflicting_start_and_start_after(func):
    with pytest.raises(TypeError):
        func(bool, start=int, start_after=bool)


def test_collect_dundermethods():
    class Parent:
        def __setitem__(self, key, value):
            pass

    class Child(Parent):
        def __len__(self):
            return 3

    dunders = collect_class_dundermethods(Child)
    assert dunders["__len__"] is Child.__len__
    assert dunders["__setitem__"] is Parent.__setitem__
    assert "__reversed__" not in dunders


def test_class_implements_dundermethod():
    class Class:
        def __len__(self):
            pass

    assert class_implements_dundermethod(Class, "__len__")


def test_class_implements_hash():
    class Class:
        __hash__ = None  # type: ignore

    assert not class_implements_dundermethod(Class, "__hash__")


def test_class_implements_dundermethod_handles_meta():
    class Meta(type):
        def __len__(self):
            pass

    class Class(metaclass=Meta):
        pass

    assert not class_implements_dundermethod(Class, "__len__")


def test_class_implements_dundermethod_with_bound():
    class Class:
        pass

    assert not class_implements_dundermethod(Class, "__init__", bound=object)


def test_class_implements_dundermethod_with_nonclass():
    with pytest.raises(TypeError):
        class_implements_dundermethod(3, "__len__")  # type: ignore


def test_class_implements_dundermethods():
    class Foo:
        def __lt__(self, other):
            return False

        def __gt__(self, other):
            return False

    assert class_implements_dundermethods(Foo, ["__lt__", "__init__"])


def test_class_implements_dundermethods_hash():
    class Foo:
        __hash__ = None  # type: ignore

    assert not class_implements_dundermethods(Foo, ["__hash__", "__init__"])


def test_class_implements_any_dundermethod():
    class Foo:
        def __lt__(self, other):
            return False

        def __gt__(self, other):
            return False

    assert class_implements_any_dundermethod(Foo, ["__gt__", "__getitem__"])


def test_class_implements_any_dundermethod_hash():
    class Foo:
        __hash__ = None  # type: ignore

    assert not class_implements_any_dundermethod(Foo, ["__hash__"])


def test_get_class_dundermethod():
    class Foo:
        def __init__(self):
            pass

    assert get_class_dundermethod(Foo, "__init__") is Foo.__init__


def test_get_class_dundermethod_error():
    with pytest.raises(AttributeError):
        get_class_dundermethod(object, "__len__")


def test_get_bound_dundermethod():
    method = get_bound_dundermethod([1, 2], "__len__")

    assert method() == 2  # type: ignore


def test_get_bound_dundermethod_handles_instance_method():
    class MySized:
        def __len__(self):
            return 3

    my_sized = MySized()
    my_sized.__len__ = lambda: 0  # type: ignore

    method = get_bound_dundermethod(my_sized, "__len__")

    assert method() == 3  # type: ignore


def test_get_bound_dundermethod_without_descriptor():
    class Callable:
        def __call__(self, *args):
            return args

    class Demo:
        __len__ = Callable()

    obj = Demo()
    method = get_bound_dundermethod(obj, "__len__")

    assert method() == ()  # type: ignore


def test_get_bound_dundermethod_error():
    with pytest.raises(AttributeError):
        get_bound_dundermethod([1, 2], "__int__")


def test_get_bound_dundermethod_noneable_error():
    class Foo:
        __hash__ = None  # type: ignore

    with pytest.raises(AttributeError):
        get_bound_dundermethod(Foo(), "__hash__")


@pytest.mark.parametrize(
    "func, obj",
    [
        (len, "foo"),
        (str, object()),
        (int, 293.5),
    ],
)
def test_dunder_module(func, obj):
    expected_result = func(obj)
    dunder_func = getattr(introspection.dunder, func.__name__)

    assert dunder_func(obj) == expected_result

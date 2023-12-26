import abc
import types

import pytest

import introspection
from introspection.classes import *
from introspection.misc import is_abstract


def test_get_subclasses():
    class A:
        pass

    class B(A):
        pass

    class C(A):
        pass

    class D(B, C):
        pass

    assert get_subclasses(A) == {B, C, D}


def test_get_subclasses_with_abstract_classes():
    class A(abc.ABC):
        @abc.abstractmethod
        def foo(self):
            pass

    class B(A):
        pass

    class C(A):
        foo = vars  # type: ignore

    class D(B, C):
        pass

    assert get_subclasses(A) == {C, D}


def test_get_subclasses_include_abstract():
    class A(abc.ABC):
        @abc.abstractmethod
        def foo(self):
            pass

    class B(A):
        pass

    class C(A):
        foo = vars  # type: ignore

    class D(B, C):
        pass

    assert get_subclasses(A, include_abstract=True) == {B, C, D}


def test_get_slot_counts_tuple():
    class Foo:
        __slots__ = ("foo", "bar")

    assert get_slot_counts(Foo) == {"foo": 1, "bar": 1}


def test_get_slot_counts_str():
    class Foo:
        __slots__ = "foo"

    assert get_slot_counts(Foo) == {"foo": 1}


def test_get_slot_counts_mangled():
    class Foo:
        __slots__ = ("__foo", "__bar__")

    assert get_slot_counts(Foo) == {"_Foo__foo": 1, "__bar__": 1}


def test_get_slot_counts_inheritance():
    class Foo:
        __slots__ = "foo"

    class Bar(Foo):
        __slots__ = ["foo", "bar"]

    assert get_slot_counts(Bar) == {"foo": 2, "bar": 1}


def test_get_slot_counts_omitted():
    class Foo:
        pass

    assert get_slot_counts(Foo) == {"__weakref__": 1, "__dict__": 1}


def test_get_slot_names():
    class Foo:
        __slots__ = "foo"

    class Bar(Foo):
        __slots__ = ["foo", "bar"]

    assert get_slot_names(Bar) == {"foo", "bar"}


def test_get_slots_inheritance():
    class Foo:
        __slots__ = "foo"

    class Bar(Foo):
        __slots__ = ["foo", "bar"]

    class Baz(Bar):
        __slots__ = ("baz",)

    slots = get_slots(Baz)
    assert len(slots) == 3
    assert slots["foo"] is Baz.foo
    assert slots["bar"] is Baz.bar
    assert slots["baz"] is Baz.baz


def test_get_attributes_slots_and_dict():
    class Foo:
        __slots__ = "foo"

    class Bar(Foo):
        pass

    obj = Bar()
    obj.foo = 3
    obj.bar = 5  # type: ignore

    assert get_attributes(obj) == {"foo": 3, "bar": 5}


def test_get_attributes_slots():
    class Foo:
        __slots__ = ["foo", "bar"]

    obj = Foo()
    obj.foo = 3
    # bar intentionally left empty

    assert get_attributes(obj) == {"foo": 3}


def test_get_attributes_with_weakref():
    class Foo:
        pass

    obj = Foo()
    obj.foo = 3  # type: ignore

    attrs = get_attributes(obj, include_weakref=True)
    assert attrs == {"foo": 3, "__weakref__": None}


@pytest.mark.parametrize(
    "method_name, expected_type",
    [
        ("__new__", staticmethod),
        ("__init_subclass__", classmethod),
        ("__class_getitem__", classmethod),
        ("__init__", None),
        ("__get__", None),
        ("frobnicate", None),
    ],
)
def test_get_implicit_method_type(method_name, expected_type):
    assert get_implicit_method_type(method_name) is expected_type


def test_add_method_to_class():
    def method(self):
        return 5

    class Foo:
        pass

    add_method_to_class(method, Foo)

    assert Foo.method is method  # type: ignore


def test_add_method_to_class_overwrite():
    def method(self):
        return 5

    class Foo:
        def method(self):
            return 3

    add_method_to_class(method, Foo)

    assert Foo.method is method


def test_add_method_to_class_with_name():
    def method(self):
        return 5

    class Foo:
        pass

    add_method_to_class(method, Foo, name="my_method")

    assert Foo.my_method is method  # type: ignore
    assert Foo().my_method() == 5  # type: ignore


def test_add_method_to_class_with_implicit_type():
    def method(cls, key):
        return (key, 2)

    class Foo:
        pass

    add_method_to_class(method, Foo, name="__class_getitem__")

    assert isinstance(vars(Foo)["__class_getitem__"], classmethod)
    assert Foo.__class_getitem__.__func__ is method  # type: ignore


def test_add_method_to_class_as_staticmethod():
    def do_something():
        pass

    class Foo:
        pass

    add_method_to_class(do_something, Foo, method_type=staticmethod)

    assert isinstance(vars(Foo)["do_something"], staticmethod)
    assert Foo.do_something is do_something  # type: ignore


def test_add_method_to_class_as_instancemethod():
    def method(self):
        return 5

    class Foo:
        pass

    add_method_to_class(method, Foo, method_type=None)

    assert Foo.method is method  # type: ignore
    assert isinstance(vars(Foo)["method"], types.FunctionType)


def test_wrap_method_instancemethod():
    def __repr__(original_method, self):
        return "hello " + original_method(self)

    class Foo:
        def __repr__(self):
            return "world"

    wrap_method(__repr__, Foo)

    assert repr(Foo()) == "hello world"


def test_wrap_method_no_original_instancemethod():
    def __repr__(original_method, self):
        return "hello " + original_method(self)

    class Parent:
        def __repr__(self):
            return "world"

    class Child(Parent):
        pass

    wrap_method(__repr__, Child)

    assert repr(Child()) == "hello world"


def test_wrap_method_implicit_classmethod():
    def init_subclass(original_method, cls, **kwargs):
        original_method(cls, **kwargs)
        cls.foo = True

    class Parent:
        def __init_subclass__(cls, **kwargs):
            cls.parent_kwargs = kwargs  # type: ignore

    class Child(Parent):
        pass

    wrap_method(init_subclass, Child, "__init_subclass__")

    class Toddler(Child, bar=9):
        pass

    assert isinstance(vars(Child)["__init_subclass__"], classmethod)
    assert Toddler.foo is True  # type: ignore
    assert Toddler.parent_kwargs == {"bar": 9}  # type: ignore


def test_wrap_method_implicit_staticmethod(monkeypatch):
    # There is no implicit staticmethod other than __new__, which gets
    # special handling, so we must monkeypatch it
    monkeypatch.setattr(introspection.classes, "get_implicit_method_type", lambda _: staticmethod)

    def do_stuff(original_method, *args, **kwargs):
        return 4, original_method(*args, **kwargs)

    class Parent:
        @staticmethod
        def do_stuff(x, *, y):
            return 17, x, y

    class Child(Parent):
        pass

    wrap_method(do_stuff, Child)

    assert isinstance(vars(Child)["do_stuff"], staticmethod)
    assert Child().do_stuff(3, y=False) == (4, (17, 3, False))


def test_wrap_method_with_explicit_type():
    def do_something(original_method, cls, *args, **kwargs):
        return (cls, original_method(*args, **kwargs))

    class Foo:
        @staticmethod
        def do_something():
            return 5

    wrap_method(do_something, Foo, method_type=classmethod)

    assert Foo.do_something() == (Foo, 5)


def test_wrap_method_no_other_new():
    def new(original_new, cls, *args, **kwargs):
        instance = original_new(cls, *args, **kwargs)
        instance.z = 3
        return instance

    # Foo doesn't define __new__, so the original_new
    # must not pass on any arguments to object.__new__
    class Parent:
        def __init__(self, x, *, y):
            self.x = x
            self.y = y

    class Child(Parent):
        pass  # another class with no __new__ method

    wrap_method(new, Parent, "__new__")

    obj = Child(1, y=2)
    assert vars(obj) == {"x": 1, "y": 2, "z": 3}


def test_wrap_method_new_with_no_init():
    def new(original_new, cls, *args, **kwargs):
        instance = original_new(cls, *args, **kwargs)
        instance.z = 3
        return instance

    # Foo doesn't define __new__ OR __init__, so calling
    # it with arguments should fail
    class Foo:
        pass

    wrap_method(new, Foo, "__new__")

    with pytest.raises(TypeError):
        Foo(1, y=2)  # type: ignore


def test_wrap_method_with_super_new():
    def new(original_new, cls, *args, **kwargs):
        instance = original_new(cls, *args, **kwargs)
        instance.z = 3
        return instance

    # Since Bar implements __new__, original_new must forward
    # its arguments
    class Bar:
        def __new__(cls, x, *, y):
            instance = super().__new__(cls)
            instance.x = x  # type: ignore
            instance.y = y  # type: ignore
            return instance

        def __init__(self, *args, **kwargs):
            pass

    class Foo(Bar):
        pass

    wrap_method(new, Foo, "__new__")

    foo = Foo(1, y=2)
    assert vars(foo) == {"x": 1, "y": 2, "z": 3}


def test_wrap_method_with_injected_super_new():
    def new(original_new, cls, *args, **kwargs):
        instance = original_new(cls, *args, **kwargs)
        instance.z = 3
        return instance

    # Neither Foo nor any of its base classes implement __new__,
    # but FooBar injects Bar (which does implement __new__) into
    # the MRO
    class Bar:
        def __new__(cls, x, *, y):
            instance = super().__new__(cls)
            instance.x = x  # type: ignore
            instance.y = y  # type: ignore
            return instance

        def __init__(self, *args, **kwargs):
            pass

    class Foo:
        pass

    class FooBar(Foo, Bar):
        pass

    wrap_method(new, Foo, "__new__")

    foo = FooBar(1, y=2)
    assert vars(foo) == {"x": 1, "y": 2, "z": 3}


def test_wrap_method_with_subclass_new():
    def new(original_new, cls, *args, **kwargs):
        instance = original_new(cls, *args, **kwargs)
        instance.z = 3
        return instance

    # Foo doesn't implement __new__, but SubFoo
    # does. So if any arguments are passed into Foo.__new__,
    # that's SubFoo.__new__'s fault. In this case, the
    # arguments should be forwarded to object.__new__ so
    # that it throws an exception.
    class Foo:
        pass

    class SubFoo(Foo):
        def __new__(cls):
            return super().__new__(cls, "oops, an extra argument")  # type: ignore

        # Add an __init__ method to stay out of the "pass on arguments
        # if the class doesn't implement __init__" branch
        def __init__(self, *args, **kwargs):
            pass

    wrap_method(new, Foo, "__new__")

    with pytest.raises(TypeError):
        SubFoo()


def test_wrap_method_with_multiple_new():
    new1_args = new1_kwargs = None

    def new1(original_new, cls, *args, **kwargs):
        nonlocal new1_args, new1_kwargs
        new1_args = args
        new1_kwargs = kwargs

        return original_new(cls, *args, **kwargs)

    def new2(original_new, cls, *args, **kwargs):
        return original_new(cls, *args, **kwargs)

    # There are multiple classes with a replaced
    # __new__ method in the MRO, so the last one
    # should handle the arguments
    class Bar:
        pass

    class Foo(Bar):
        pass

    wrap_method(new1, Bar, "__new__")
    wrap_method(new2, Foo, "__new__")

    with pytest.raises(TypeError):
        Foo("oops", what="are these doing here")  # type: ignore

    assert new1_args == ("oops",)
    assert new1_kwargs == {"what": "are these doing here"}


def test_wrap_method_typeerror():
    with pytest.raises(TypeError):
        # 2nd argument must be a class
        wrap_method(repr, len)  # type: ignore


def test_is_abstract_class():
    class Foo:
        @abc.abstractmethod
        def func(self):
            pass

    class Bar(Foo):
        def func(self):
            pass

    assert is_abstract(Foo)
    assert not is_abstract(Bar)


def test_get_abstract_method_names():
    class A:
        class AbstractNestedClass(abc.ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        def concrete_method(self):
            pass

        @abc.abstractmethod
        def abstract_instance_method(self):
            pass

        @abc.abstractmethod
        def implemented_instance_method(self):
            pass

        @classmethod
        @abc.abstractmethod
        def abstract_classmethod(cls):
            pass

        @staticmethod
        @abc.abstractmethod
        def abstract_staticmethod():
            pass

        @property
        @abc.abstractmethod
        def abstract_property(self):
            pass

        @property
        def another_abstract_property(self):
            pass

        @another_abstract_property.deleter
        @abc.abstractmethod
        def another_abstract_property(self):
            pass

        @property
        @abc.abstractmethod
        def implemented_property(self):
            pass

    class B(A):
        @classmethod
        def concrete_classmethod(cls):
            pass

        def implemented_instance_method(self):
            pass

        @A.implemented_property.getter
        def implemented_property(self):
            pass

    assert get_abstract_method_names(B) == {
        "abstract_instance_method",
        "abstract_classmethod",
        "abstract_staticmethod",
        "abstract_property",
        "another_abstract_property",
    }


@pytest.mark.parametrize(
    "method",
    [
        staticmethod(lambda: None),
        classmethod(lambda: None),  # type: ignore
    ],
)
def test_fit_to_class_method(method):
    class Foo:
        pass

    fit_to_class(method, Foo, "new-name")
    func = method.__func__

    assert func.__module__ == Foo.__module__
    assert func.__name__ == "new-name"
    assert func.__qualname__ == Foo.__qualname__ + ".new-name"


@pytest.mark.parametrize(
    "prop",
    [
        property(lambda: None),  # type: ignore
        property(fset=lambda: None),  # type: ignore
        property(fdel=lambda: None),  # type: ignore
        property(lambda: None, lambda: None, lambda: None),  # type: ignore
    ],
)
def test_fit_to_class_property(prop):
    class Foo:
        pass

    fit_to_class(prop, Foo, "new-name")

    for func in [prop.fget, prop.fset, prop.fdel]:
        if func is None:
            continue

        assert func.__module__ == Foo.__module__
        assert func.__name__ == "new-name"
        assert func.__qualname__ == Foo.__qualname__ + ".new-name"

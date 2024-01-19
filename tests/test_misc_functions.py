import pytest

import abc
import collections
import sys
import typing

from introspection import *
from introspection import errors
import introspection


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
    assert attrs == {"x": 4}


@pytest.mark.xfail
def test_static_vars_with_shadowed_dict():
    class Foo:
        def __init__(self):
            self.x = 4

        __dict__ = None  # type: ignore

    foo = Foo()
    attrs = static_vars(foo)
    assert attrs == {"x": 4}


def test_static_hasattr_instance_attr():
    class Foo:
        pass

    foo = Foo()
    foo.bar = 17  # type: ignore

    assert static_hasattr(foo, "bar")


def test_static_hasattr_class_attr():
    class Foo:
        __slots__ = ["bar"]

    assert static_hasattr(Foo(), "bar")


def test_static_hasattr_metaclass_attr():
    class Meta(type):
        def bar(cls):
            pass

    class Class(metaclass=Meta):
        pass

    assert static_hasattr(Class, "bar")


@pytest.mark.parametrize(
    "obj",
    [
        3,
        collections.UserList(),
        collections.UserDict,  # the class, not an instance
    ],
)
def test_static_hasattr_with_missing_attr(obj):
    assert not static_hasattr(obj, "bar")


def test_static_copy():
    class Foo:
        __slots__ = ["foo", "__dict__"]

    foo = Foo()
    foo.foo = []

    foo_copy = static_copy(foo)

    assert type(foo_copy) is type(foo)
    assert foo_copy.foo is foo.foo
    assert "bar"


def test_static_copy_empty_slot():
    class Foo:
        __slots__ = ["foo", "bar"]

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

    assert "attr" not in vars(foo_copy)


def test_static_copy_is_shallow():
    class Foo:
        pass

    foo = Foo()
    foo.bar = []  # type: ignore

    foo_copy = static_copy(foo)

    assert foo_copy.bar is foo.bar  # type: ignore


def test_static_copy_builtin():
    foo = [1, 2]
    foo_copy = static_copy(foo)

    assert foo_copy == foo
    assert foo_copy is not foo


@pytest.mark.parametrize(
    "classes,ancestor",
    [
        ([], object),
        ([str], str),
        ([int, bool], int),
        ([bool, int], int),
        ([int, float], object),
        ([Exception, IndexError, LookupError], Exception),
    ],
)
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

    assert resolve_bases(bases) == (list, int, 5)  # type: ignore


@pytest.mark.parametrize(
    "metaclass",
    [
        type,
        abc.ABCMeta,
    ],
)
def test_create_class(metaclass):
    cls = create_class(
        "MyClass",
        (typing.List,),
        {"x": 5},
        metaclass=metaclass,
    )

    assert cls.__name__ == "MyClass"
    assert isinstance(cls, metaclass)
    assert issubclass(cls, list)
    assert cls.x == 5  # type: ignore


def test_create_class_no_meta():
    class MROEntries:
        def __mro_entries__(self, bases):
            return (list,)

    cls = create_class("MyClass", (MROEntries(),))  # type: ignore

    assert cls.__name__ == "MyClass"
    assert type(cls) is type
    assert issubclass(cls, list)


def test_create_class_no_mro_entries():
    cls = create_class("MyClass", (list,))

    assert cls.__name__ == "MyClass"
    assert type(cls) is type
    assert issubclass(cls, list)


def test_iter_wrapped_with_staticmethod():
    def foo():
        pass

    def bar():
        pass

    bar.__wrapped__ = foo
    static_bar = staticmethod(bar)

    assert list(iter_wrapped(static_bar)) == [bar, foo]  # type: ignore


def test_iter_wrapped_with_stop():
    def foo():
        pass

    def bar():
        pass

    def baz():
        pass

    bar.__wrapped__ = foo
    baz.__wrapped__ = bar

    stop = lambda func: func.__name__ == "foo"

    assert list(iter_wrapped(baz, stop)) == [baz, bar]


@pytest.mark.parametrize(
    "container, expected_result",
    [
        (classmethod(len), [len]),  # type: ignore
        (staticmethod(repr), [repr]),
        (property(), []),
        (property(len, repr), [len, repr]),  # type: ignore
    ],
)
def test_extract_functions(container, expected_result):
    assert extract_functions(container) == expected_result


@pytest.mark.parametrize(
    "obj",
    [
        None,
        123,
        classmethod,
        staticmethod,
        property,
        type,
    ],
)
def test_extract_functions_typeerror(obj):
    with pytest.raises(TypeError):
        extract_functions(obj)


def test_rename_function():
    func = lambda: None

    rename(func, "frobnicate")

    assert func.__name__ == "frobnicate"
    assert func.__qualname__ == "test_rename_function.<locals>.frobnicate"


def test_rename_class():
    class Foo:
        def foo(self):
            pass

    class Bar(Foo):
        def bar(self):
            pass

        foo_ref = Foo.foo

        @property
        def prop(self):
            pass

        @prop.setter
        def prop(self, value):
            pass

        @staticmethod
        def static_method():
            pass

        @classmethod
        def class_method(cls):
            pass

    rename(Bar, "Qux")

    assert Bar.__name__ == "Qux"
    assert Bar.__qualname__ == "test_rename_class.<locals>.Qux"

    assert Bar.foo.__qualname__ == "test_rename_class.<locals>.Foo.foo"
    assert Bar.foo_ref.__qualname__ == "test_rename_class.<locals>.Foo.foo"
    assert Bar.bar.__qualname__ == "test_rename_class.<locals>.Qux.bar"
    assert Bar.prop.fget.__qualname__ == "test_rename_class.<locals>.Qux.prop"
    assert Bar.prop.fset.__qualname__ == "test_rename_class.<locals>.Qux.prop"
    assert (
        vars(Bar)["static_method"].__func__.__qualname__
        == "test_rename_class.<locals>.Qux.static_method"
    )
    assert (
        vars(Bar)["class_method"].__func__.__qualname__
        == "test_rename_class.<locals>.Qux.class_method"
    )

    if sys.version_info >= (3, 10):
        assert (
            vars(Bar)["static_method"].__qualname__
            == "test_rename_class.<locals>.Qux.static_method"
        )
        assert (
            vars(Bar)["class_method"].__qualname__ == "test_rename_class.<locals>.Qux.class_method"
        )


def test_wraps():
    def foo(a, b, c):
        pass

    foo.__module__ = "somewhere_else"

    @wraps(foo)
    def bar(*args, **kwargs):
        pass

    assert bar.__wrapped__ is foo
    assert bar.__name__ == "foo"
    assert bar.__qualname__ == "test_wraps.<locals>.foo"
    assert bar.__module__ == foo.__module__
    assert str(signature(bar)) == "(a, b, c)"


def test_wraps_with_extra_kwargs():
    def foo(a, b, c):
        pass

    foo.__module__ = "somewhere_else"

    @wraps(foo, name="qux", remove_parameters=[2, "a"])
    def bar(*args, **kwargs):
        pass

    assert bar.__wrapped__ is foo
    assert bar.__name__ == "qux"
    assert bar.__qualname__ == "test_wraps_with_extra_kwargs.<locals>.qux"
    assert bar.__module__ == foo.__module__
    assert str(signature(bar)) == "(b)"


def test_wraps_with_signature():
    def foo(a, b, c):
        pass

    qux = lambda a, b, c: None

    @wraps(foo, signature=signature(qux), remove_parameters=[2, "a"])
    def bar(*args, **kwargs):
        pass

    assert bar.__wrapped__ is foo
    assert bar.__name__ == foo.__name__
    assert bar.__qualname__ == foo.__qualname__
    assert bar.__module__ == foo.__module__
    assert str(signature(bar)) == "(b)"


def test_wraps_with_signature_from_function():
    def foo(a):
        pass

    qux = lambda a, b, c: None

    @wraps(foo, signature=qux)
    def bar(*args, **kwargs):
        pass

    assert bar.__wrapped__ is foo
    assert bar.__name__ == foo.__name__
    assert bar.__qualname__ == foo.__qualname__
    assert bar.__module__ == foo.__module__
    assert str(signature(bar)) == "(a, b, c)"


def test_super():
    results = [None, None]

    class Descriptor:
        def __get__(self, instance, owner):
            return (self, instance, owner)

        def __set__(self, instance, value):
            results[0] = (self, instance, value)  # type: ignore

        def __delete__(self, instance):
            results[1] = (self, instance)  # type: ignore

    desc = Descriptor()

    class Parent:
        pass

    Parent.desc = desc  # type: ignore

    class Child(Parent):
        pass

    obj = Child()
    sup = introspection.super(Child, obj)

    assert sup.desc == (desc, obj, Child)  # type: ignore
    sup.desc = 7
    del sup.desc

    assert results[0] == (desc, obj, 7)
    assert results[1] == (desc, obj)


def test_super_with_2_classes():
    class Descriptor:
        def __set__(self, instance, owner):
            pass

        def __delete__(self, instance):
            pass

    class Parent:
        desc = Descriptor()

    class Child(Parent):
        pass

    sup = introspection.super(Child, Child)

    with pytest.raises(AttributeError):
        sup.desc = 7

    with pytest.raises(AttributeError):
        del sup.desc


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("builtins.int", int),
        ("builtins.float.is_integer", float.is_integer),
    ],
)
def test_resolve_identifier(identifier, expected):
    assert resolve_identifier(identifier) is expected


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "not-builtins",
        "builtins.frank",
    ],
)
def test_resolve_identifier_error(identifier):
    with pytest.raises(errors.InvalidIdentifier):
        resolve_identifier(identifier)

    # Deprecated exception
    with pytest.raises(NameError):
        resolve_identifier(identifier)


@pytest.mark.parametrize(
    "sub_name, super_name, expected",
    [
        ("foo", "foo", True),
        ("foo.bar", "foo", True),
        ("foo.bar", "foo.bar", True),
        ("foo", "foo.bar", False),
        ("foo", "bar.foo", False),
    ],
)
def test_is_sub_qualname(sub_name, super_name, expected):
    assert is_sub_qualname(sub_name, super_name) == expected


@pytest.mark.parametrize(
    "camel, expected",
    [
        ("FooBar", "foo_bar"),
        ("HTTPAdapter", "http_adapter"),
    ],
)
def test_camel_to_snake(camel, expected):
    assert camel_to_snake(camel) == expected


@pytest.mark.parametrize(
    "snake, expected",
    [
        ("foo_bar", "FooBar"),
        ("http_adapter", "HttpAdapter"),
    ],
)
def test_snake_to_camel(snake, expected):
    assert snake_to_camel(snake) == expected

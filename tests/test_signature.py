import pytest

import builtins
import functools
import inspect
import typing as t

import introspection
from introspection import Signature, Parameter, errors


def test_get_signature():
    def foo(a, b=3) -> str:
        return ""

    sig = Signature.from_callable(foo)
    assert sig.return_annotation is str
    assert len(sig.parameters) == 2
    assert list(sig.parameters) == ["a", "b"]
    assert sig.parameters["a"].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters["a"].default == Parameter.empty
    assert sig.parameters["b"].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters["b"].default == 3


def test_get_int_signature():
    sig = Signature.from_callable(int)
    assert sig.return_annotation is int
    assert len(sig.parameters) == 2
    assert list(sig.parameters) == ["x", "base"]
    assert sig.parameters["x"].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters["x"].default in {0, Parameter.missing}
    assert sig.parameters["base"].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters["base"].default in {10, Parameter.missing}


def test_get_float_signature():
    sig = Signature.from_callable(float)
    assert sig.return_annotation is float
    assert len(sig.parameters) == 1
    assert list(sig.parameters) == ["x"]
    assert sig.parameters["x"].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters["x"].default in {0, Parameter.missing}


def test_get_bool_signature():
    sig = Signature.from_callable(bool)
    assert sig.return_annotation is bool
    assert len(sig.parameters) == 1
    assert list(sig.parameters) == ["x"]
    assert sig.parameters["x"].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters["x"].default is Parameter.missing


def test_get_signature_undoc_c_function():
    c_function = iter

    try:
        inspect.signature(c_function)
    except ValueError:
        pass
    else:
        pytest.fail(
            f"{c_function} is no longer suitable for this test."
            f" We need `inspect.signature` to throw a `ValueError`"
        )

    with pytest.raises(errors.NoSignatureFound):
        Signature.from_callable(c_function, use_signature_db=False)

    # Deprecated exception
    with pytest.raises(ValueError):
        Signature.from_callable(c_function, use_signature_db=False)


def test_get_signature_noncallable():
    with pytest.raises(TypeError):
        Signature.from_callable(123)  # type: ignore


def test_signature_with_optional_parameter():
    sig = Signature.from_callable(vars)

    assert sig.return_annotation is dict
    assert len(sig.parameters) == 1
    assert sig.parameters["object"].annotation is t.Any
    assert sig.parameters["object"].default is Parameter.missing


def test_store_signature():
    def foo(a=5) -> str:
        return "bar"

    sig = Signature.from_callable(foo)
    foo.__signature__ = sig  # type: ignore

    s = inspect.signature(foo)
    assert s is sig


BUILTIN_CALLABLES = {
    name: obj
    for name, obj in vars(builtins).items()
    if callable(obj) and obj.__module__ == "builtins"
}


@pytest.mark.parametrize(
    "callable_",
    BUILTIN_CALLABLES.values(),
    ids=BUILTIN_CALLABLES.keys(),
)
def test_builtin_signatures(callable_: t.Callable):
    try:
        _ = Signature.from_callable(callable_)
    except Exception as e:
        pytest.fail(
            f"Couldn't obtain signature of {callable_.__name__!r}: {e!r}."
            f" It must be added to the signature database."
        )


def test_follow_wrapped():
    @functools.lru_cache(None)
    def func(x, y):
        pass

    sig = introspection.signature(func)
    assert list(sig.parameters) == ["x", "y"]


def test_dont_follow_wrapped():
    def noop_deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @noop_deco
    def func(x, y):
        pass

    sig = introspection.signature(func, follow_wrapped=False)
    assert list(sig.parameters) == ["args", "kwargs"]


def test_bound_method_signature():
    class A:
        def method(self, foo: int) -> str:
            return "hi"

    obj = A()
    sig = introspection.signature(obj.method)

    assert list(sig.parameters) == ["foo"]
    assert sig.return_annotation is str
    assert sig.parameters["foo"].annotation is int
    assert sig.parameters["foo"].kind is Parameter.POSITIONAL_OR_KEYWORD


def test_decorated_bound_method_signature():
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    class A:
        @deco
        def method(self, foo: int) -> str:
            return "hi"

    obj = A()
    sig = introspection.signature(obj.method)

    assert list(sig.parameters) == ["foo"]
    assert sig.return_annotation is str
    assert sig.parameters["foo"].annotation is int
    assert sig.parameters["foo"].kind is Parameter.POSITIONAL_OR_KEYWORD


def test_method_signature():
    class A:
        def method(self, foo: int = 3) -> None:
            pass

    class B(A):
        def method(self, *args, bar: bool = True, **kwargs):
            return super().method(*args, **kwargs)

    sig = Signature.for_method(B, "method")
    assert list(sig.parameters) == ["self", "foo", "bar"]
    assert sig.return_annotation is None
    assert sig.parameters["foo"].annotation is int
    assert sig.parameters["foo"].default == 3
    assert sig.parameters["foo"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters["bar"].annotation is bool
    assert sig.parameters["bar"].default is True
    assert sig.parameters["bar"].kind is Parameter.KEYWORD_ONLY


def test_method_signature_with_repeated_argument():
    class A:
        def method(self, foo: int = 3) -> None:
            pass

    class B(A):
        def method(self, *args, foo: float = 3.5, **kwargs):
            return super().method(*args, foo=int(foo), **kwargs)

    sig = Signature.for_method(B, "method")
    assert list(sig.parameters) == ["self", "foo"]
    assert sig.return_annotation is None
    assert sig.parameters["foo"].annotation is float
    assert sig.parameters["foo"].default == 3.5
    assert sig.parameters["foo"].kind is Parameter.KEYWORD_ONLY


def test_class_signature():
    class Cls:
        def __init__(self, init):
            pass

    sig = Signature.from_callable(Cls)
    assert list(sig.parameters) == ["init"]


def test_class_signature_with_no_constructor():
    class Cls:
        pass

    sig = Signature.from_callable(Cls)
    assert list(sig.parameters) == []


def test_class_signature_with_metaclass():
    class Meta(type):
        def __call__(self, meta):  # type: ignore (invalid override)
            pass

    class Cls(metaclass=Meta):
        def __new__(cls, new):
            pass

        def __init__(self, init):
            pass

    sig = Signature.from_callable(Cls)
    assert list(sig.parameters) == ["meta"]


def test_skip_metaclass_signature():
    class Meta(type):
        @introspection.mark.does_not_alter_signature
        def __call__(cls, *args, **kwargs):
            return super().__call__(*args, **kwargs)

    class Cls(metaclass=Meta):
        def __init__(self, foo):
            pass

    sig = Signature.from_callable(Cls)
    assert list(sig.parameters) == ["foo"]


def test_partial():
    def func(x, *y, z):
        pass

    part = functools.partial(func, 1, 2, 3, z=4)
    sig = Signature.from_callable(part)
    assert list(sig.parameters) == ["y", "z"]
    assert sig.parameters["y"].kind is Parameter.VAR_POSITIONAL
    assert sig.parameters["z"].default == 4


def test_partial_and_skip_metaclass_signature():
    class Meta(type):
        @introspection.mark.does_not_alter_signature
        def __call__(cls, *args, **kwargs):
            return super().__call__(*args, **kwargs)

    class Cls(metaclass=Meta):
        def __init__(self, foo, bar: "int"):
            pass

    sig = Signature.from_callable(functools.partial(Cls, 3))
    assert list(sig.parameters) == ["bar"]


def test_builtin_class_signature():
    # Just make sure it doesn't crash
    _ = Signature.from_callable(float, use_signature_db=False)


def test_custom_callable():
    class CustomCallable:
        def __call__(self, param: str):
            pass

    sig = Signature.from_callable(CustomCallable())
    assert list(sig.parameters) == ["param"]
    assert sig.parameters["param"].annotation is str


def test_custom_callable_with_different_modules():
    from collections import UserString

    class CustomCallable:
        def __call__(self, param: "UserString"):
            pass

    # Pretend the `__call__` was inherited from a base class that was defined somewhere else
    CustomCallable.__module__ = "sys"
    CustomCallable.__call__.__module__ = "collections"

    sig = Signature.from_callable(CustomCallable())
    assert list(sig.parameters) == ["param"]
    assert sig.forward_ref_context == "collections"


def test_doesnt_alter_signature_mark():
    class Cls:
        @introspection.mark.does_not_alter_signature
        def __new__(cls, *args, **kwargs):
            return super().__new__(cls, *args, **kwargs)

        def __init__(self, init):
            pass

    sig = Signature.from_callable(Cls)
    assert list(sig.parameters) == ["init"]


def test_replace():
    sig = Signature([Parameter("foo")], return_annotation=int)

    expected = Signature(return_annotation=str)

    result = sig.replace(parameters=[], return_annotation=str)
    assert isinstance(result, Signature)
    assert result == expected


def test_without_parameters():
    sig = Signature([Parameter("foo"), Parameter("bar"), Parameter("baz")])

    expected = Signature([Parameter("bar")])

    result = sig.without_parameters(0, "baz")
    assert result == expected


def test_num_required_arguments():
    sig = Signature(
        [
            Parameter("a", Parameter.POSITIONAL_ONLY),
            Parameter("b", Parameter.VAR_POSITIONAL),
            Parameter("c", Parameter.KEYWORD_ONLY),
            Parameter("d", Parameter.VAR_KEYWORD),
        ]
    )

    assert sig.num_required_arguments == 2


@pytest.mark.parametrize(
    "func, args, kwargs, expected_result",
    [
        ((lambda a, b: 0), ["A", "B"], {}, {"a": "A", "b": "B"}),
        ((lambda a, *, b: 0), ["A"], {"b": "B"}, {"a": "A", "b": "B"}),
        ((lambda a, b="B": 0), ["A"], {}, {"a": "A"}),
        ((lambda a, b="X": 0), ["A"], {"b": "B"}, {"a": "A", "b": "B"}),
        ((lambda a, b="B": 0), ["A"], {}, {"a": "A"}),
        ((lambda *a, b="B": 0), ["A", "B"], {}, {"a": ("A", "B")}),
        ((lambda *a, b="B", **c: 0), ["A", "B"], {"d": "D"}, {"a": ("A", "B"), "c": {"d": "D"}}),
    ],
)
def test_bind(func, args, kwargs, expected_result):
    sig = Signature.from_callable(func)
    assert sig.bind(*args, **kwargs).arguments == expected_result


@pytest.mark.parametrize(
    "func, args, kwargs, expected_result",
    [
        ((lambda a, b: 0), ["A", "B"], {}, {"a": "A", "b": "B"}),
        ((lambda a, *, b: 0), ["A"], {"b": "B"}, {"a": "A", "b": "B"}),
        ((lambda a, b="B": 0), ["A"], {}, {"a": "A"}),
        ((lambda a, b="X": 0), ["A"], {"b": "B"}, {"a": "A", "b": "B"}),
        ((lambda a, b="B": 0), ["A"], {}, {"a": "A"}),
        ((lambda *a, b="B": 0), ["A", "B"], {}, {"a": ("A", "B")}),
        ((lambda *a, b="B", **c: 0), ["A", "B"], {"d": "D"}, {"a": ("A", "B"), "c": {"d": "D"}}),
    ],
)
def test_bind_partial(func, args, kwargs, expected_result):
    sig = Signature.from_callable(func)
    assert sig.bind_partial(*args, **kwargs).arguments == expected_result


@pytest.mark.parametrize(
    "signature, expected",
    [
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY),
                    Parameter("b", Parameter.VAR_POSITIONAL),
                ]
            ),
            "(a, /, *b)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY),
                    Parameter("b", Parameter.POSITIONAL_ONLY),
                ]
            ),
            "(a, b, /)",
        ),
        (Signature([Parameter("a", default=Parameter.missing)]), "([a])"),
        (
            Signature([Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing)]),
            "([a], /)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", default=Parameter.missing),
                ]
            ),
            "([a], /[, b])",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                ]
            ),
            "([a[, b]], /)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", Parameter.POSITIONAL_ONLY, default=5),
                    Parameter("c", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                ]
            ),
            "([a, b=5[, c]], /)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("c", Parameter.POSITIONAL_ONLY, default=3),
                ]
            ),
            "([a[, b, c=3]], /)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("c", Parameter.POSITIONAL_OR_KEYWORD, default=Parameter.missing),
                ]
            ),
            "([a[, b]], /[, c])",
        ),
        (Signature([Parameter("a"), Parameter("b", default=Parameter.missing)]), "(a[, b])"),
        (
            Signature(
                [
                    Parameter("a", default=Parameter.missing),
                    Parameter("b", default=Parameter.missing),
                ]
            ),
            "([a][, b])",
        ),
        (Signature([Parameter("a"), Parameter("b", Parameter.KEYWORD_ONLY)]), "(a, *, b)"),
        (Signature([Parameter("a", Parameter.KEYWORD_ONLY)]), "(*, a)"),
        (
            Signature(
                [Parameter("a", Parameter.KEYWORD_ONLY), Parameter("b", Parameter.KEYWORD_ONLY)]
            ),
            "(*, a, b)",
        ),
        (
            Signature([Parameter("a", Parameter.KEYWORD_ONLY, default=Parameter.missing)]),
            "(*[, a])",
        ),
        (Signature([Parameter("a", Parameter.VAR_POSITIONAL)]), "(*a)"),
        (Signature([Parameter("a", Parameter.VAR_KEYWORD)]), "(**a)"),
        (Signature([Parameter("a", Parameter.POSITIONAL_ONLY)]), "(a, /)"),
        (Signature([Parameter("a", Parameter.POSITIONAL_ONLY), Parameter("b")]), "(a, /, b)"),
        (
            Signature(
                [Parameter("a", Parameter.POSITIONAL_ONLY), Parameter("b", Parameter.KEYWORD_ONLY)]
            ),
            "(a, /, *, b)",
        ),
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY, default=Parameter.missing),
                    Parameter("b", Parameter.KEYWORD_ONLY, default=Parameter.missing),
                ]
            ),
            "([a], /, *[, b])",
        ),
        (Signature([Parameter("x", annotation=int)], return_annotation=str), "(x: int) -> str"),
        (Signature([Parameter("x", annotation=bool, default=False)]), "(x: bool = False)"),
        (
            Signature([Parameter("x", annotation=tuple)], return_annotation=t.Tuple),
            "(x: tuple) -> typing.Tuple",
        ),
        (
            Signature(return_annotation=t.Tuple[int, t.List]),
            "() -> typing.Tuple[int, typing.List]",
        ),
    ],
)
def test_to_string(signature: Signature, expected: str):
    assert signature.to_string() == expected


@pytest.mark.parametrize(
    "signature, expected",
    [
        (
            Signature(
                [
                    Parameter("a", Parameter.POSITIONAL_ONLY),
                    Parameter("b", Parameter.VAR_POSITIONAL),
                ],
                return_annotation=str,
            ),
            "<Signature (a, /, *b) -> str>",
        ),
    ],
)
def test_repr(signature, expected):
    assert repr(signature) == expected

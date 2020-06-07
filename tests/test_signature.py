
import pytest

import functools
import inspect
import sys
import typing

import introspection
from introspection import Signature, Parameter


def make_fake_c_function(doc, monkeypatch):
    # Functions written in C don't have signatures; we'll
    # fake one by creating an object with a __doc__ attribute
    def fake_sig(*a, **kw):
        raise ValueError
    monkeypatch.setattr(inspect, 'signature', fake_sig)
    monkeypatch.setattr(sys.modules['introspection.signature'], 'callable', lambda _: True, raising=False)

    class FakeFunction:
        pass

    fake_func = FakeFunction()
    fake_func.__doc__ = doc
    return fake_func


def test_get_signature():
    def foo(a, b=3) -> str:
        pass

    sig = Signature.from_callable(foo)
    assert sig.return_annotation is str
    assert len(sig.parameters) == 2
    assert list(sig.parameters) == ['a', 'b']
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['b'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['b'].default == 3


def test_get_int_signature():
    sig = Signature.from_callable(int)
    assert sig.return_annotation is int
    assert len(sig.parameters) == 2
    assert list(sig.parameters) == ['x', 'base']
    assert sig.parameters['x'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['x'].default in {0, Parameter.missing}
    assert sig.parameters['base'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['base'].default in {10, Parameter.missing}


def test_get_float_signature():
    sig = Signature.from_callable(float)
    assert sig.return_annotation is float
    assert len(sig.parameters) == 1
    assert list(sig.parameters) == ['x']
    assert sig.parameters['x'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['x'].default in {0, Parameter.missing}


def test_get_bool_signature():
    sig = Signature.from_callable(bool)
    assert sig.return_annotation is bool
    assert len(sig.parameters) == 1
    assert list(sig.parameters) == ['x']
    assert sig.parameters['x'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['x'].default is Parameter.missing


def test_get_signature_undoc_c_function(monkeypatch):
    fake_func = make_fake_c_function(None, monkeypatch)

    with pytest.raises(ValueError):
        Signature.from_callable(fake_func)


def test_get_signature_noncallable():
    with pytest.raises(TypeError):
        Signature.from_callable(3)


def test_signature_with_optional_parameter():
    sig = Signature.from_callable(vars)

    assert sig.return_annotation is dict
    assert len(sig.parameters) == 1
    assert sig.parameters['object'].annotation is typing.Any
    assert sig.parameters['object'].default is Parameter.missing


def test_store_signature():
    def foo(a=5) -> str:
        return 'bar'

    sig = Signature.from_callable(foo)
    foo.__signature__ = sig

    s = inspect.signature(foo)
    assert s is sig


def test_signature_from_class_with_init():
    class Foo:
        def __init__(self, x, y=3):
            pass

    sig = Signature.from_class(Foo)
    assert list(sig.parameters) == ['x', 'y']


def test_signature_from_class_with_new():
    class Foo:
        def __new__(cls, x, y=3):
            pass

    sig = Signature.from_class(Foo)
    assert list(sig.parameters) == ['x', 'y']


def test_signature_from_class_with_new_and_init():
    class Foo:
        def __new__(cls, *args, y, **kwargs):
            pass

        def __init__(self, x, y):
            pass

    sig = Signature.from_class(Foo)
    assert list(sig.parameters) == ['x', 'y']
    assert sig.parameters['y'].kind == Parameter.KEYWORD_ONLY


def test_signature_from_class_with_new_and_init_and_meta():
    class Meta(type):
        def __call__(cls, x, *args):
            pass

    class Foo(metaclass=Meta):
        def __new__(cls, *args):
            pass

        def __init__(self, x, y):
            pass

    sig = Signature.from_class(Foo)
    assert list(sig.parameters) == ['x', 'y']
    assert sig.parameters['x'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['y'].kind == Parameter.POSITIONAL_ONLY


def test_signature_from_class_with_new_and_init_positional_only():
    class Foo:
        def __new__(cls, *args, y):
            pass

        def __init__(self, x, y):
            pass

    sig = Signature.from_class(Foo)
    assert list(sig.parameters) == ['x', 'y']
    assert sig.parameters['x'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['y'].kind == Parameter.KEYWORD_ONLY


def test_signature_from_class_with_conflicting_new_and_init():
    class Foo:
        def __new__(cls, x, y):
            pass

        def __init__(self):
            pass

    with pytest.raises(ValueError):
        _ = Signature.from_class(Foo)


def test_builtin_signatures():
    import builtins

    for thing in vars(builtins).values():
        if not callable(thing):
            continue

        try:
            _ = Signature.from_callable(thing)
        except Exception as e:
            msg = "Couldn't obtain signature of {!r}: {!r}"
            pytest.fail(msg.format(thing, e))


def test_follow_wrapped():
    @functools.lru_cache(None)
    def func(x, y):
        pass

    sig = introspection.signature(func)
    assert list(sig.parameters) == ['x', 'y']


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
    assert list(sig.parameters) == ['args', 'kwargs']


def test_num_required_arguments():
    sig = Signature([
        Parameter('a', Parameter.POSITIONAL_ONLY),
        Parameter('b', Parameter.VAR_POSITIONAL),
        Parameter('c', Parameter.KEYWORD_ONLY),
        Parameter('d', Parameter.VAR_KEYWORD)
    ])

    assert sig.num_required_arguments == 2


def test_iteration():
    param = Parameter('foo')
    sig = Signature([param])

    assert list(sig) == [param]


@pytest.mark.parametrize('signatures, expected', [
    ([Signature(return_annotation=int),
      Signature(return_annotation=float)],
     Signature(return_annotation=typing.Union[int, float])
    ),
    ([Signature(return_annotation=int),
      Signature(return_annotation=bool)],
     Signature(return_annotation=int)
    ),
    ([Signature(return_annotation=int),
      Signature(return_annotation=float),
      Signature(return_annotation=bool)],
     Signature(return_annotation=typing.Union[int, float])
    ),
    ([Signature(return_annotation=list),
      Signature(return_annotation=typing.List)],
     Signature(return_annotation=list)
    ),
    ([Signature(return_annotation=list),
      Signature(return_annotation=typing.List[str]),
      Signature(return_annotation=typing.List)],
     Signature(return_annotation=list)
    ),
    ([Signature([Parameter('a')], return_annotation=int),
      Signature([Parameter('b', Parameter.KEYWORD_ONLY, default=3)], return_annotation=float)],
     Signature([Parameter('a'), Parameter('b', Parameter.KEYWORD_ONLY, default=3)], return_annotation=typing.Union[int, float])
    ),
])
def test_union(signatures, expected):
    merged = signatures[0].union(*signatures[1:])
    assert merged == expected


@pytest.mark.parametrize('signature, expected', [
    (Signature([Parameter('a', default=Parameter.missing)]), '([a])'),
    (Signature([Parameter('a', Parameter.POSITIONAL_ONLY, default=Parameter.missing)]), '([a], /)'),
    (Signature([Parameter('a'), Parameter('b', default=Parameter.missing)]), '(a[, b])'),
    (Signature([Parameter('a'), Parameter('b', Parameter.KEYWORD_ONLY)]), '(a, *, b)'),
    (Signature([Parameter('a', Parameter.KEYWORD_ONLY)]), '(*, a)'),
    (Signature([Parameter('a', Parameter.KEYWORD_ONLY, default=Parameter.missing)]), '(*[, a])'),
    (Signature([Parameter('a', Parameter.VAR_POSITIONAL)]), '(*a)'),
    (Signature([Parameter('a', Parameter.VAR_KEYWORD)]), '(**a)'),
    (Signature([Parameter('a', Parameter.POSITIONAL_ONLY)]), '(a, /)'),
    (Signature([Parameter('a', Parameter.POSITIONAL_ONLY), Parameter('b')]), '(a, /, b)'),
    (Signature([Parameter('a', Parameter.POSITIONAL_ONLY), Parameter('b', Parameter.KEYWORD_ONLY)]), '(a, /, *, b)'),
    (Signature([Parameter('a', Parameter.POSITIONAL_ONLY, default=Parameter.missing), Parameter('b', Parameter.KEYWORD_ONLY, default=Parameter.missing)]), '([a], /, *[, b])'),
    (Signature([Parameter('x', annotation=int)], return_annotation=str), '(x: int) -> str'),
    (Signature([Parameter('x', annotation=bool, default=False)]), '(x: bool = False)'),
    (Signature([Parameter('x', annotation=tuple)], return_annotation=typing.Tuple), '(x: tuple) -> Tuple'),
    (Signature(return_annotation=typing.Tuple[int, typing.List]), '() -> Tuple[int, List]'),
])
def test_to_string(signature, expected):
    assert signature.to_string() == expected

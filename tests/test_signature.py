
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


def test_get_signature_c_function(monkeypatch):
    fake_func = make_fake_c_function("""
    __build_class__(func, name, /, *bases, [metaclass], **kwds) -> class
    """, monkeypatch)

    sig = Signature.from_callable(fake_func)
    assert sig.return_annotation is type
    assert len(sig.parameters) == 5
    assert sig.parameters['func'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['name'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['bases'].kind == Parameter.VAR_POSITIONAL
    assert sig.parameters['metaclass'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['kwds'].kind == Parameter.VAR_KEYWORD


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


def test_signature_from_docstring_with_optionals():
    doc = '''range(stop) -> range object
range(start, stop[, step]) -> range object

Return an object that produces a sequence of integers from start (inclusive)
to stop (exclusive) by step.'''

    sig = Signature.from_docstring(doc)

    parameters = list(sig.parameters.values())
    assert len(parameters) == 3
    # assert parameters[0].name == 'start_or_stop'
    assert parameters[0].default is Parameter.empty
    assert parameters[1].default is Parameter.missing
    assert parameters[2].default is Parameter.missing
    assert sig.return_annotation is range


def test_signature_from_docstring_without_returntype():
    doc = '''float(x=0)'''

    sig = Signature.from_docstring(doc)

    parameters = list(sig.parameters.values())
    assert len(parameters) == 1
    assert parameters[0].name == 'x'
    assert parameters[0].default == 0
    assert sig.return_annotation is object


def test_signature_from_docstring_with_positional_only_args():
    doc = '''float(x=0, /, y=1)'''

    sig = Signature.from_docstring(doc)

    parameters = list(sig.parameters.values())
    assert len(parameters) == 2
    assert parameters[0].name == 'x'
    assert parameters[0].default == 0
    assert parameters[0].kind is Parameter.POSITIONAL_ONLY
    assert parameters[1].name == 'y'
    assert parameters[1].default == 1
    assert parameters[1].kind is Parameter.POSITIONAL_OR_KEYWORD


def test_signature_from_docstring_with_varargs():
    doc = '''foo(x, *, y) -> foo'''

    sig = Signature.from_docstring(doc)

    parameters = list(sig.parameters.values())
    assert len(parameters) == 2
    assert parameters[0].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1].kind is Parameter.KEYWORD_ONLY


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

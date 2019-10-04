
import inspect

from introspection import Signature, Parameter



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


def test_signature_with_optional_parameter():
    sig = Signature.from_callable(vars)

    assert sig.return_annotation is dict
    assert len(sig.parameters) == 1
    assert sig.parameters['object'].annotation is object
    assert sig.parameters['object'].default is Parameter.missing


def test_store_signature():
    def foo(a=5) -> str:
        return 'bar'

    sig = Signature.from_callable(foo)
    foo.__signature__ = sig

    s = inspect.signature(foo)
    assert s is sig

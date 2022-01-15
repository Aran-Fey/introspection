
from xml.etree.ElementPath import xpath_tokenizer_re
import pytest

import inspect
from introspection import Signature, BoundArguments


def test_bound_args_from_bound_arguments():
    sig = inspect.signature(lambda a, b, *c: None)
    bound_args = sig.bind('A', 'B', 'C', 'D')

    bound_args = BoundArguments.from_bound_arguments(bound_args)

    assert bound_args.arguments == {'a': 'A', 'b': 'B', 'c': ('C', 'D')}


@pytest.mark.parametrize('func, args, kwargs, expected_args, expected_kwargs', [
    ((lambda a, b, c:0), [9, 8, 7], {}, [9, 8, 7], {}),
    ((lambda a, b, c:0), [9, 8], {}, [9, 8], {}),
    ((lambda *b, c:0), [9, 8], {'c': 7}, [9, 8], {'c': 7}),
    (range, [9, 8, 7], {}, [9, 8, 7], {}),
    ((lambda a, *b, c:0), [9], {'c': 7}, [9], {'c': 7}),
    ((lambda a, *b, **c:0), [9, 8, 7], {'foo': 'bar'}, [9, 8, 7], {'foo': 'bar'}),
])
def test_to_varargs_prefer_args(func, args, kwargs, expected_args, expected_kwargs):
    sig = Signature.from_callable(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    args, kwargs = bound_args.to_varargs(prefer='args')

    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize('func, args, kwargs, expected_args, expected_kwargs', [
    ((lambda a, b, c:0), [9, 8, 7], {}, [], {'a': 9, 'b': 8, 'c': 7}),
    ((lambda a, b, c:0), [9, 8], {}, [], {'a': 9, 'b': 8}),
    ((lambda *b, c:0), [9, 8], {'c': 7}, [9, 8], {'c': 7}),
    (range, [9, 8, 7], {}, [9, 8, 7], {}),
    ((lambda a, *b, c:0), [9], {'c': 7}, [], {'a': 9, 'c': 7}),
    ((lambda a, *b, **c:0), [9, 8, 7], {'foo': 'bar'}, [9, 8, 7], {'foo': 'bar'}),
])
def test_to_varargs_prefer_kwargs(func, args, kwargs, expected_args, expected_kwargs):
    sig = Signature.from_callable(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    args, kwargs = bound_args.to_varargs(prefer='kwargs')

    assert args == expected_args
    assert kwargs == expected_kwargs


def test_to_varargs_invalid_prefer_arg():
    bound_args = Signature.from_callable(lambda x: x).bind(3)

    with pytest.raises(ValueError):
        bound_args.to_varargs(prefer='foobar')

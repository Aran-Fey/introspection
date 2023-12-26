import pytest

import inspect
from introspection import Signature, BoundArguments


def test_bound_args_from_bound_arguments():
    sig = inspect.signature(lambda a, b, *c: None)
    bound_args = sig.bind("A", "B", "C", "D")

    bound_args = BoundArguments.from_bound_arguments(bound_args)

    assert bound_args.arguments == {"a": "A", "b": "B", "c": ("C", "D")}


@pytest.mark.parametrize(
    "func, args, kwargs, expected_args, expected_kwargs",
    [
        ((lambda a, b, c: 0), [9, 8, 7], {}, [9, 8, 7], {}),
        ((lambda a, b, c: 0), [9, 8], {}, [9, 8], {}),
        ((lambda *b, c: 0), [9, 8], {"c": 7}, [9, 8], {"c": 7}),
        (range, [9, 8, 7], {}, [9, 8, 7], {}),
        ((lambda a, *b, c: 0), [9], {"c": 7}, [9], {"c": 7}),
        ((lambda a, *b, **c: 0), [9, 8, 7], {"foo": "bar"}, [9, 8, 7], {"foo": "bar"}),
    ],
)
def test_to_varargs_prefer_args(func, args, kwargs, expected_args, expected_kwargs):
    sig = Signature.from_callable(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    args, kwargs = bound_args.to_varargs(prefer="args")

    assert args == expected_args
    assert kwargs == expected_kwargs


@pytest.mark.parametrize(
    "func, args, kwargs, expected_args, expected_kwargs",
    [
        ((lambda a, b, c: 0), [9, 8, 7], {}, [], {"a": 9, "b": 8, "c": 7}),
        ((lambda a, b, c: 0), [9, 8], {}, [], {"a": 9, "b": 8}),
        ((lambda *b, c: 0), [9, 8], {"c": 7}, [9, 8], {"c": 7}),
        (range, [9, 8, 7], {}, [9, 8, 7], {}),
        ((lambda a, *b, c: 0), [9], {"c": 7}, [], {"a": 9, "c": 7}),
        ((lambda a, *b, **c: 0), [9, 8, 7], {"foo": "bar"}, [9, 8, 7], {"foo": "bar"}),
    ],
)
def test_to_varargs_prefer_kwargs(func, args, kwargs, expected_args, expected_kwargs):
    sig = Signature.from_callable(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    args, kwargs = bound_args.to_varargs(prefer="kwargs")

    assert args == expected_args
    assert kwargs == expected_kwargs


def test_to_varargs_invalid_prefer_arg():
    bound_args = Signature.from_callable(lambda x: x).bind(3)

    with pytest.raises(ValueError):
        bound_args.to_varargs(prefer="foobar")  # type: ignore


def test_iter():
    bound_args = Signature.from_callable(lambda x, y, z: x).bind_partial(3, 4)

    assert tuple(bound_args) == ("x", "y")


def test_len():
    bound_args = Signature.from_callable(lambda x, y: x).bind_partial(3)

    assert len(bound_args) == 1


def test_getitem():
    bound_args = Signature.from_callable(lambda x: x).bind(3)

    assert bound_args["x"] == 3


def test_getitem_keyerror():
    bound_args = Signature.from_callable(lambda x: x).bind(3)

    with pytest.raises(KeyError):
        bound_args["y"]


def test_setitem():
    bound_args = Signature.from_callable(lambda x: x).bind(3)

    bound_args["x"] = 17
    assert bound_args["x"] == 17


@pytest.mark.parametrize(
    "func, args, kwargs, expected",
    [
        (lambda x: 0, [], {}, {"x"}),
        (lambda x=3: 0, [], {}, set()),
        (lambda x: 0, [3], {}, set()),
    ],
)
def test_get_missing_parameter_names(func, args, kwargs, expected):
    bound_args = Signature.from_callable(func).bind_partial(*args, **kwargs)

    assert bound_args.get_missing_parameter_names() == expected


@pytest.mark.parametrize(
    "func, args, kwargs, expected",
    [
        (lambda x=3: 0, [], {}, {"x"}),
        (lambda *args: 0, [], {}, set()),
        (lambda **kwargs: 0, [], {}, set()),
    ],
)
def test_get_missing_parameter_names_with_optionals(func, args, kwargs, expected):
    bound_args = Signature.from_callable(func).bind_partial(*args, **kwargs)

    result = bound_args.get_missing_parameter_names(include_optional_parameters=True)
    assert result == expected

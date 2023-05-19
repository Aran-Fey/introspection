
import pytest

import inspect
import typing

from introspection import Parameter


@pytest.mark.parametrize('param1, param2, expected', [
    (inspect.Parameter('a', Parameter.POSITIONAL_ONLY), Parameter('a', Parameter.POSITIONAL_ONLY), True),
    (Parameter('a', Parameter.POSITIONAL_ONLY), inspect.Parameter('a', Parameter.POSITIONAL_ONLY), True),
    (inspect.Parameter('not_a', Parameter.POSITIONAL_ONLY), Parameter('a', Parameter.POSITIONAL_ONLY), False),
    (inspect.Parameter('a', Parameter.VAR_KEYWORD), Parameter('a', Parameter.VAR_KEYWORD), True),
])
def test_equality(param1, param2, expected):
    hash_equal = hash(param1) == hash(param2)
    assert hash_equal == expected

    equal = param1 == param2
    assert equal == expected


def test_from_inspect_parameter():
    in_param = inspect.Parameter('foo', Parameter.KEYWORD_ONLY, default=object(), annotation=int)
    param = Parameter.from_parameter(in_param)

    assert in_param == param


def test_from_parameter():
    in_param = Parameter('foo', Parameter.KEYWORD_ONLY, object(), int)
    param = Parameter.from_parameter(in_param)

    assert in_param == param


@pytest.mark.parametrize('attrs', [
    {'name': 'bar'},
    {'kind': Parameter.VAR_KEYWORD},
    {'default': 3},
    {'annotation': list},
    {'default': 5, 'annotation': complex}
])
def test_replace(attrs):
    param = Parameter('foo')

    param = param.replace(**attrs)

    assert isinstance(param, Parameter)

    for key, value in attrs.items():
        assert getattr(param, key) == value


@pytest.mark.parametrize('kind, expected', [
    (Parameter.POSITIONAL_ONLY, False),
    (Parameter.VAR_POSITIONAL, True),
    (Parameter.POSITIONAL_OR_KEYWORD, False),
    (Parameter.VAR_KEYWORD, True),
    (Parameter.KEYWORD_ONLY, False),
])
def test_is_vararg(kind, expected):
    param = Parameter('foo', kind)

    assert param.is_vararg == expected


@pytest.mark.parametrize('param, expected', [
    (Parameter('a', Parameter.POSITIONAL_ONLY, default=3), True),
    (Parameter('a', Parameter.POSITIONAL_OR_KEYWORD, default=Parameter.missing), True),
    (Parameter('a', Parameter.POSITIONAL_OR_KEYWORD, default=Parameter.empty), False),
    (Parameter('a', Parameter.VAR_POSITIONAL), True),
    (Parameter('a', Parameter.VAR_KEYWORD), True),
    (Parameter('a', Parameter.POSITIONAL_ONLY), False),
    (Parameter('a', Parameter.POSITIONAL_OR_KEYWORD), False),
])
def test_is_optional(param, expected):
    assert param.is_optional == expected


@pytest.mark.parametrize('param, expected', [
    (Parameter('foo'), 'foo'),
    (Parameter('foo', Parameter.VAR_POSITIONAL), '*foo'),
    (Parameter('foo', Parameter.VAR_KEYWORD), '**foo'),
    (Parameter('foo', default=3), 'foo=3'),
    (Parameter('foo', default=[]), 'foo=[]'),
    (Parameter('foo', default=Parameter.missing), '[foo]'),
    (Parameter('foo', annotation=int), 'foo: int'),
    (Parameter('foo', annotation=typing.List[int]), 'foo: typing.List[int]'),
    (Parameter('foo', annotation=None), 'foo: None'),
    (Parameter('foo', default=5, annotation=int), 'foo: int = 5'),
    (Parameter('foo', default=Parameter.missing, annotation=int), '[foo: int]'),
    (Parameter('foo', Parameter.POSITIONAL_ONLY, default=5), 'foo=5, /'),
    (Parameter('foo', Parameter.POSITIONAL_ONLY, default=Parameter.missing), '[foo], /'),
])
def test_to_string(param, expected):
    assert param.to_string() == expected


@pytest.mark.parametrize('param, expected', [
    (Parameter('foo', Parameter.VAR_KEYWORD), '<Parameter **foo>'),
])
def test_repr(param, expected):
    assert repr(param) == expected

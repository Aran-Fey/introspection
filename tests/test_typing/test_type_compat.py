
import pytest

import collections.abc
import typing

from introspection.typing.type_compat import *


@pytest.mark.parametrize('type_, expected', [
    (int, int),
    (None, None),
    (typing.List, list),
    (typing.Set, set),
    (typing.Callable, collections.abc.Callable),
    (typing.List[typing.Any], list),
    (typing.Callable[..., typing.Any], collections.abc.Callable),
    (typing.Type[object], type),
])
def test_to_python_strict(type_, expected):
    assert to_python(type_, strict=True) == expected


@pytest.mark.parametrize('type_, expected', [
    (typing.Any, typing.Any),
    (typing.SupportsFloat, typing.SupportsFloat),
    (typing.List[int], typing.List[int]),
    (typing.List[typing.Set], typing.List[set]),
    (typing.List[typing.Set[typing.Tuple]], typing.List[typing.Set[tuple]]),
    (typing.Callable[[typing.Set], typing.Tuple], typing.Callable[[set], tuple]),
    (typing.Callable[..., typing.List], typing.Callable[..., list])
])
def test_to_python_non_strict(type_, expected):
    assert to_python(type_, strict=False) == expected


@pytest.mark.parametrize('type_', [
    typing.Any,
    typing.SupportsFloat,
    typing.List[typing.SupportsFloat],
])
def test_to_python_strict_error(type_):
    with pytest.raises(ValueError):
        to_python(type_, strict=True)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_to_python_error(type_):
    with pytest.raises(TypeError):
        to_python(type_)


@pytest.mark.parametrize('type_, expected', [
    (list, typing.List),
    (set, typing.Set),
    (collections.abc.Callable, typing.Callable),
    (object, object),
    (typing.Any, typing.Any),
    ('set', typing.Set),
    (typing.Callable, typing.Callable),
    (typing.List[set], typing.List[typing.Set]),
    (typing.List['re.Match'], typing.List[typing.Match]),
    (typing.Callable[..., 'collections.defaultdict'], typing.Callable[..., typing.DefaultDict]),
    (typing.Callable[['set'], 'collections.defaultdict'], typing.Callable[[typing.Set], typing.DefaultDict]),
])
def test_to_typing(type_, expected):
    assert to_typing(type_) == expected


@pytest.mark.parametrize('type_', [
    'Foo',
    Exception,
])
def test_to_typing_strict_error(type_):
    with pytest.raises(ValueError):
        to_typing(type_, strict=True)



if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, typing.Literal),
        (typing.Literal[1, 2], typing.Literal[1, 2]),
    ])
    def test_literal_to_python(type_, expected):
        assert to_python(type_, strict=False) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, typing.Literal),
        (typing.Literal[1, 2], typing.Literal[1, 2]),
    ])
    def test_literal_to_typing(type_, expected):
        assert to_typing(type_, strict=True) == expected

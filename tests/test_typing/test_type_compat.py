
import pytest

import collections.abc
import re
import sys
import typing

from introspection.typing.type_compat import *
from introspection import errors


T = typing.TypeVar('T')

class MyGeneric(typing.Generic[T]):
    pass


is_py39_plus = sys.version_info >= (3, 9)


@pytest.mark.parametrize('type_, expected', [
    (int, int),
    (None, None),
    (typing.List, list),
    (typing.Set, set),
    (typing.Callable, collections.abc.Callable),
    (MyGeneric, MyGeneric),
    (typing.List[typing.Any], list),
    (typing.Callable[..., typing.Any], collections.abc.Callable),
    (typing.Type[object], type),
    (MyGeneric[typing.Tuple], MyGeneric[tuple]),
    (MyGeneric[typing.Any], MyGeneric),
])
def test_to_python_strict(type_, expected):
    assert to_python(type_, strict=True) == expected


@pytest.mark.parametrize('type_, expected', [
    (typing.Any, typing.Any),
    (typing.SupportsFloat, typing.SupportsFloat),
    (typing.Optional[int], typing.Optional[int]),
])
def test_to_python_non_strict(type_, expected):
    assert to_python(type_, strict=False) == expected


@pytest.mark.parametrize('type_', [
    typing.Any,
    typing.SupportsFloat,
    typing.List[typing.SupportsFloat],
])
def test_to_python_strict_error(type_):
    with pytest.raises(errors.NoPythonEquivalent):
        to_python(type_, strict=True)
    
    # Deprecated exception
    with pytest.raises(ValueError):
        to_python(type_, strict=True)


if is_py39_plus:
    @pytest.mark.parametrize('type_, expected', [
        (typing.List[int], list[int]),
        (typing.Match[str], re.Match[str]),
        (typing.List[typing.Set], list[set]),
        (typing.List[typing.Set[typing.Tuple]], list[set[tuple]]),
        (typing.Callable[[typing.Set], typing.Tuple], collections.abc.Callable[[set], tuple]),
        (typing.Callable[..., typing.List], collections.abc.Callable[..., list]),
    ])
    def test_to_python_non_strict_py39(type_, expected):
        assert to_python(type_, strict=False) == expected
else:
    @pytest.mark.parametrize('type_, expected', [
        (typing.List[int], typing.List[int]),
        (typing.List[typing.Set], typing.List[set]),
        (typing.List[typing.Set[typing.Tuple]], typing.List[typing.Set[tuple]]),
        (typing.Callable[[typing.Set], typing.Tuple], typing.Callable[[set], tuple]),
        (typing.Callable[..., typing.List], typing.Callable[..., list])
    ])
    def test_to_python_non_strict_pre39(type_, expected):
        assert to_python(type_, strict=False) == expected


    @pytest.mark.parametrize('type_', [
        typing.List[int],
    ])
    def test_to_python_strict_error_pre39(type_):
        with pytest.raises(errors.NoPythonEquivalent):
            to_python(type_, strict=True)
        
        # Deprecated exception
        with pytest.raises(ValueError):
            to_python(type_, strict=True)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_to_python_error(type_):
    with pytest.raises(errors.NotAType):
        to_python(type_)
    
    # Deprecated exception
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


if is_py39_plus:
    @pytest.mark.parametrize('type_, expected', [
        (collections.abc.Iterable[int], typing.Iterable[int]),
        (re.Pattern[bytes], typing.Pattern[bytes]),
    ])
    def test_to_typing_py39(type_, expected):
        assert to_typing(type_) == expected


@pytest.mark.parametrize('type_', [
    'Foo',
    Exception,
])
def test_to_typing_strict_error(type_):
    with pytest.raises(errors.NoTypingEquivalent):
        to_typing(type_, strict=True)
    
    # Deprecated exception
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

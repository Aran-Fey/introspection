
import pytest

import typing

from introspection.typing import *


T_co = typing.TypeVar('T_co', covariant=True)
E = typing.TypeVar('E', bound=Exception)


class MyGeneric(typing.Generic[E]):
    pass


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, False),
    (typing.Any, False),
    (typing.List, True),
    (typing.Union, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (MyGeneric, True),
    (typing.List[int], False),
    (typing.Union[int, str], False),
    (typing.Callable[[], int], False),
    (typing.Optional[int], False),
    (typing.ByteString, False),
    (typing.List[E], True),
    (MyGeneric[E], True),
    (MyGeneric[int], False),
    (typing.List[typing.Tuple[E]], True),
    (typing.List[typing.Tuple], False),
    (typing.List[typing.Callable[[E], int]], True),
    (typing.List[typing.Callable], False),
])
def test_is_generic(type_, expected):
    assert is_generic(type_) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, True),
        (typing.Literal[1, 2], False),
    ])
    def test_literal_is_generic(type_, expected):
        assert is_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    ...,
])
def test_is_generic_error(type_):
    with pytest.raises(TypeError):
        is_generic(type_)


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, False),
    (typing.Any, False),
    (typing.List, True),
    (typing.Union, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (typing.Literal, True),
    (MyGeneric, True),
    (typing.List[int], False),
    (typing.Union[int, str], False),
    (typing.Callable[[], int], False),
    (typing.Optional[int], False),
    (typing.ByteString, False),
    (typing.List[E], False),
    (MyGeneric[E], False),
])
def test_is_generic_class(type_, expected):
    assert is_generic_class(type_) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, True),
        (typing.Literal[1, 2], False),
        (typing.Literal[1, E], False),
    ])
    def test_literal_is_generic_class(type_, expected):
        assert is_generic_class(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    ...,
])
def test_is_generic_class_error(type_):
    with pytest.raises(TypeError):
        is_generic_class(type_)


@pytest.mark.parametrize(['type_', 'expected'], [
    (int, False),
    (list, False),
    (typing.Any, False),
    (typing.List, False),
    (typing.Union, False),
    (typing.Callable, False),
    (typing.Optional, False),
    (MyGeneric, False),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (MyGeneric[str], True),
    (MyGeneric[E], True),
    (typing.List[E], True),
    (typing.List[typing.List[E]], True),
])
def test_is_qualified_generic(type_, expected):
    assert is_qualified_generic(type_) == expected


@pytest.mark.parametrize(['type_', 'expected'], [
    (int, False),
    (list, False),
    (typing.Any, False),
    (typing.List, False),
    (typing.Union, False),
    (typing.Callable, False),
    (typing.Optional, False),
    (MyGeneric, False),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (MyGeneric[str], True),
    (typing.List[E], False),
    (typing.List[typing.List[E]], False),
])
def test_is_fully_qualified_generic(type_, expected):
    assert is_fully_qualified_generic(type_) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, False),
        (typing.Literal[1, 2], True),
    ])
    def test_literal_is_fully_qualified_generic(type_, expected):
        assert is_fully_qualified_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    ...,
])
def test_is_fully_qualified_generic_error(type_):
    with pytest.raises(TypeError):
        is_fully_qualified_generic(type_)


@pytest.mark.parametrize('type_, expected', [
    (typing.List[int], typing.List),
    (typing.List[E], typing.List),
    (typing.Union[int, str], typing.Union),
    (typing.Callable[[], int], typing.Callable),
    (typing.Optional[int], typing.Optional),
])
def test_get_generic_base_class(type_, expected):
    assert get_generic_base_class(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    typing.List,
    typing.Tuple,
    typing.Optional,
    typing.Union,
    typing.Callable,
])
def test_get_generic_base_class_error(type_):
    with pytest.raises(TypeError):
        get_generic_base_class(type_)


@pytest.mark.parametrize('type_, expected', [
    (typing.List[int], (int,)),
    (typing.Union[int, str], (int, str)),
    (typing.Callable[[], int], ([], int)),
    (typing.Callable[[str], int], ([str], int)),
    (typing.Callable[..., int], (..., int)),
    (typing.Optional[int], (int,)),
    (typing.List[E], (E,)),
    (typing.Generator[E, int, E][str], (str, int, str)),
    (typing.Tuple[E, int, E][str], (str, int, str)),
    (typing.Callable[[E, int], E][str], ([str, int], str)),
])
def test_get_type_args(type_, expected):
    assert get_type_args(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    typing.List,
    typing.Tuple,
    typing.Optional,
    typing.Union,
    typing.Callable,
])
def test_get_type_args_error(type_):
    with pytest.raises(TypeError):
        get_type_args(type_)


@pytest.mark.parametrize('type_, expected', [
    (typing.List, '(~T,)'),
    # (typing.Union, '()'),
    # (typing.Callable, '()'),
    # (typing.Optional, '()'),
    # (typing.Tuple, '()'),
    (typing.List[E], '(~E,)'),
    (typing.List[int], '()'),
    (typing.Generator[E, int, E], '(~E,)'),
    (typing.Tuple[E, int, T_co], '(~E, +T_co)'),
    (typing.Callable[[E, int], E][T_co], '(+T_co,)'),
    (typing.Tuple[typing.List[T_co]], '(+T_co,)'),
])
def test_get_type_params(type_, expected):
    params = get_type_params(type_)
    assert str(params) == expected


@pytest.mark.parametrize('type_, expected', [
    (int, 'int'),
    (typing.Any, 'Any'),
    (typing.List, 'List'),
    (typing.Tuple, 'Tuple'),
    (typing.Union, 'Union'),
    (typing.Optional, 'Optional'),
    (typing.Callable, 'Callable'),
    (typing.TypeVar, 'TypeVar'),
])
def test_get_type_name(type_, expected):
    assert get_type_name(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    typing.List[int],
    typing.Tuple[int, str],
    typing.Optional[str],
    typing.Union[int, float],
    typing.Callable[..., None],
])
def test_get_type_name_error(type_):
    with pytest.raises(TypeError):
        get_type_name(type_)

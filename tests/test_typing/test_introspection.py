
import pytest

import collections.abc
import re
import sys
import typing

from introspection.typing import *
from introspection.typing._compat import ForwardRef, Protocol


is_py39_plus = sys.version_info >= (3, 9)


T_co = typing.TypeVar('T_co', covariant=True)
E = typing.TypeVar('E', bound=Exception)


class MyGeneric(typing.Generic[E]):
    pass


class UnhashableMeta(type):
    __hash__ = None
class UnhashableClass(metaclass=UnhashableMeta):
    pass


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, False),
    (None, False),
    (UnhashableClass, False),
    (typing.List, False),
    ('Foo', True),
    (ForwardRef('Foo'), True),
])
def test_is_forwardref(type_, expected):
    assert is_forwardref(type_) == expected


@pytest.mark.parametrize('obj', [
    3,
    ...,
])
def test_is_forwardref_error(obj):
    with pytest.raises(TypeError):
        is_forwardref(obj)


@pytest.mark.parametrize('obj', [
    3,
    ...,
])
def test_is_forwardref_non_raising(obj):
    assert not is_forwardref(obj, raising=False)


@pytest.mark.parametrize('type_, expected', [
    (int, True),
    (list, True),
    (UnhashableClass, True),
    (None, True),
    (..., False),
    (3, False),
    ([], False),
    ('Foo', True),  # this is a forward reference
    (T_co, True),
    (E, True),
    (typing.Any, True),
    (typing.List, True),
    (typing.Union, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (typing.Type, True),
    (typing.NoReturn, True),
    (MyGeneric, True),
    (typing.TypeVar, True),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (typing.ByteString, True),
    (typing.List[E], True),
    (MyGeneric[E], True),
    (MyGeneric[int], True),
    (typing.List[typing.Tuple[E]], True),
    (typing.List[typing.Tuple], True),
    (typing.List[typing.Callable[[E], int]], True),
    (typing.List[typing.Callable], True),
])
def test_is_type(type_, expected):
    assert is_type(type_) == expected


@pytest.mark.parametrize('type_, expected', [
    ('Foo', False),
    (ForwardRef('Foo'), False),
])
def test_is_type_no_forwardref(type_, expected):
    assert is_type(type_, allow_forwardref=False) == expected


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, False),
    (UnhashableClass, False),
    (None, False),
    ('List', False),
    (ForwardRef('List'), False),
    (T_co, True),
    (E, True),
    (typing.Any, True),
    (typing.List, True),
    (typing.Union, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (typing.Type, True),
    (typing.NoReturn, True),
    (MyGeneric, False),
    (typing.TypeVar, True),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (typing.ByteString, True),
    (typing.List[E], True),
    (MyGeneric[E], True),
    (MyGeneric[int], True),
    (typing.List[typing.Tuple[E]], True),
    (typing.List[typing.Tuple], True),
    (typing.List[typing.Callable[[E], int]], True),
    (typing.List[typing.Callable], True),
])
def test_is_typing_type(type_, expected):
    assert is_typing_type(type_, raising=True) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_typing_type_error(type_):
    with pytest.raises(TypeError):
        is_typing_type(type_, raising=True)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_typing_type_non_raising(type_):
    assert not is_typing_type(type_, raising=False)


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (None, False),
    ('List', False),
    (list, is_py39_plus),
    (tuple, is_py39_plus),
    (UnhashableClass, False),
    (collections.deque, is_py39_plus),
    (collections.Counter, is_py39_plus),
    (collections.abc.Iterable, is_py39_plus),
    (collections.abc.Callable, is_py39_plus),
    (collections.abc.Sized, False),
    (typing.Any, False),
    (typing.List, True),
    (typing.Union, True),
    (typing.Tuple, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (typing.Type, True),
    (MyGeneric, True),
    (typing.List[int], False),
    (typing.Union[int, str], False),
    (typing.Tuple[int], False),
    (typing.Callable[[], int], False),
    (typing.Optional[int], False),
    (typing.ByteString, False),
    (typing.List[E], True),
    (typing.Tuple[E], True),
    (MyGeneric[E], True),
    (MyGeneric[int], False),
    (typing.List[typing.Tuple[E]], True),
    (typing.List[typing.Tuple], False),
    (typing.List[typing.Callable[[E], int]], True),
    (typing.List[typing.Callable], False),
])
def test_is_generic(type_, expected):
    assert is_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_generic_error(type_):
    with pytest.raises(TypeError):
        is_generic(type_)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_generic_non_raising(type_):
    assert not is_generic(type_, raising=False)


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, False),
    (tuple, is_py39_plus),
    (UnhashableClass, False),
    (collections.abc.Callable, False),
    (None, False),
    ('List', False),
    (typing.Any, False),
    (typing.Union, True),
    (typing.Tuple, True),
    (typing.List, False),
    (typing.Callable, False),
    (typing.Optional, False),
    (typing.Type, False),
    (MyGeneric, False),
    (typing.List[int], False),
    (typing.Union[int, str], False),
    (typing.Tuple[int], False),
    (typing.Callable[[], int], False),
    (typing.Optional[int], False),
    (typing.ByteString, False),
    (typing.List[E], False),
    (typing.Tuple[E], False),
    (MyGeneric[E], False),
    (MyGeneric[int], False),
    (typing.List[typing.Tuple[E]], False),
    (typing.List[typing.Tuple], False),
    (typing.List[typing.Callable[[E], int]], False),
    (typing.List[typing.Callable], False),
])
def test_is_variadic_generic(type_, expected):
    assert is_variadic_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_variadic_generic_error(type_):
    with pytest.raises(TypeError):
        is_variadic_generic(type_)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_variadic_generic_non_raising(type_):
    assert not is_variadic_generic(type_, raising=False)


@pytest.mark.parametrize('type_, expected', [
    (int, False),
    (list, is_py39_plus),
    (tuple, is_py39_plus),
    (UnhashableClass, False),
    (None, False),
    ('List', False),
    (collections.defaultdict, is_py39_plus),
    (collections.Counter, is_py39_plus),
    (collections.abc.Iterator, is_py39_plus),
    (collections.abc.Callable, is_py39_plus),
    (collections.abc.Sized, False),
    (typing.Any, False),
    (typing.List, True),
    (typing.Union, True),
    (typing.Callable, True),
    (typing.Optional, True),
    (typing.Type, True),
    (MyGeneric, True),
    (typing.List[int], False),
    (typing.Union[int, str], False),
    (typing.Callable[[], int], False),
    (typing.Optional[int], False),
    (typing.ByteString, False),
    (typing.List[E], False),
    (MyGeneric[E], False),
])
def test_is_generic_base_class(type_, expected):
    assert is_generic_base_class(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_generic_base_class_error(type_):
    with pytest.raises(TypeError):
        is_generic_base_class(type_)


@pytest.mark.parametrize(['type_', 'expected'], [
    (int, False),
    (list, False),
    (UnhashableClass, False),
    (None, False),
    ('List', False),
    (typing.Any, False),
    (typing.List, False),
    (typing.Union, False),
    (typing.Callable, False),
    (typing.Optional, False),
    (typing.Type, False),
    (MyGeneric, False),
    (typing.Type[str], True),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (MyGeneric[str], True),
    (MyGeneric[E], True),
    (typing.List[E], True),
    (typing.List[typing.Tuple[E]], True),
])
def test_is_parameterized_generic(type_, expected):
    assert is_parameterized_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_parameterized_generic_error(type_):
    with pytest.raises(TypeError):
        is_parameterized_generic(type_)


if is_py39_plus:
    @pytest.mark.parametrize(['type_', 'expected'], [
        (type[str], True),
        (list[int], True),
        (re.Pattern[str], True),
        (re.Match[bytes], True),
        (collections.Counter[str], True),
        (collections.defaultdict[int, E], True),
        (list[E], True),
        (list[tuple[E]], True),
    ])
    def test_is_parameterized_generic_py39(type_, expected):
        assert is_parameterized_generic(type_) == expected


@pytest.mark.parametrize(['type_', 'expected'], [
    (int, False),
    (list, False),
    (UnhashableClass, False),
    (None, False),
    ('List', False),
    (collections.abc.Iterable, False),
    (collections.abc.Callable, False),
    (collections.abc.ByteString, is_py39_plus),
    (typing.Any, False),
    (typing.List, False),
    (typing.Union, False),
    (typing.Callable, False),
    (typing.Optional, False),
    (typing.ByteString, True),
    (MyGeneric, False),
    (typing.Type[int], True),
    (typing.List[int], True),
    (typing.Union[int, str], True),
    (typing.Callable[[], int], True),
    (typing.Optional[int], True),
    (MyGeneric[str], True),
    (typing.List[E], False),
    (typing.List[typing.List[E]], False),
])
def test_is_fully_parameterized_generic(type_, expected):
    assert is_fully_parameterized_generic(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_fully_parameterized_generic_error(type_):
    with pytest.raises(TypeError):
        is_fully_parameterized_generic(type_)


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_is_fully_parameterized_generic_non_raising(type_):
    assert not is_fully_parameterized_generic(type_, raising=False)


if is_py39_plus:
    @pytest.mark.parametrize(['type_', 'expected'], [
        (type[str], True),
        (list[int], True),
        (tuple[int], True),
        (tuple[E], False),
        (list[E], False),
        (list[tuple[E]], False),
        (tuple[list[int]], True),
        (tuple[list[E]], False),
        (re.Pattern[str], True),
        (re.Match[bytes], True),
        (collections.Counter[str], True),
        (collections.defaultdict[int, E], False),
        (collections.abc.Iterable[str], True),
        (collections.abc.Iterable[E], False),
    ])
    def test_is_fully_parameterized_generic_py39(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


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
    ...,
    'List',
    list,
    UnhashableClass,
    collections.abc.Iterable,
    collections.abc.Callable,
    typing.List,
    typing.Tuple,
    typing.Optional,
    typing.Union,
    typing.Callable,
    typing.Type,
])
def test_get_generic_base_class_error(type_):
    with pytest.raises(TypeError):
        get_generic_base_class(type_)


if is_py39_plus:
    @pytest.mark.parametrize('type_, expected', [
        (list[int], list),
        (list[E], list),
        (tuple[list[str]], tuple),
        (re.Pattern[str], re.Pattern),
        (re.Match[bytes], re.Match),
        (collections.deque[int], collections.deque),
        (collections.abc.Iterator[str], collections.abc.Iterator),
    ])
    def test_get_generic_base_class_py39(type_, expected):
        assert get_generic_base_class(type_) == expected


@pytest.mark.parametrize('type_, expected', [
    (typing.List[int], (int,)),
    (typing.Union[int, str], (int, str)),
    (typing.Callable[[], int], ([], int)),
    (typing.Callable[[str], int], ([str], int)),
    (typing.Callable[..., int], (..., int)),
    (typing.Optional[int], (int,)),
    (typing.Type[str], (str,)),
    (typing.List[E], (E,)),
    (typing.Generator[E, int, E][str], (str, int, str)),
    (typing.Tuple[E, int, E][str], (str, int, str)),
    (typing.Callable[[E, int], E][str], ([str, int], str)),
    (typing.Tuple[typing.List[E]][str], (typing.List[str],)),
    (typing.Tuple[typing.List[typing.Type[E]]][str], (typing.List[typing.Type[str]],)),
])
def test_get_type_arguments(type_, expected):
    assert get_type_arguments(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    None,
    'List',
    typing.List,
    typing.Tuple,
    typing.Optional,
    typing.Union,
    typing.Callable,
    typing.Type,
])
def test_get_type_arguments_error(type_):
    with pytest.raises(TypeError):
        get_type_arguments(type_)


if is_py39_plus:
    @pytest.mark.parametrize('type_, expected', [
        (list[int], (int,)),
        (collections.abc.Callable[[], int], ([], int)),
        (collections.abc.Callable[[str], int], ([str], int)),
        (collections.abc.Callable[..., int], (..., int)),
        (type[str], (str,)),
        (list[E], (E,)),
        (collections.abc.Generator[E, int, E][str], (str, int, str)),
        (tuple[E, int, E][str], (str, int, str)),
        (collections.abc.Callable[[E, int], E][str], ([str, int], str)),
        (tuple[list[E]][str], (list[str],)),
        (tuple[list[type[E]]][str], (list[type[str]],)),
    ])
    def test_get_type_arguments_py39(type_, expected):
        assert get_type_arguments(type_) == expected


@pytest.mark.parametrize('type_, expected', [
    (typing.List, '(~T,)'),
    (typing.Union, '(+T_co,)'),
    (typing.Callable, '(-A_contra, +R_co)'),
    (typing.Optional, '(+T_co,)'),
    (typing.Tuple, '(+T_co,)'),
    (typing.Type, '(+CT_co,)'),
    (typing.ByteString, '()'),
    (typing.List[E], '(~E,)'),
    (typing.List[int], '()'),
    (typing.Generator[E, int, E], '(~E,)'),
    (typing.Tuple[E, int, T_co], '(~E, +T_co)'),
    (typing.Callable[[E, int], E][T_co], '(+T_co,)'),
    (typing.Tuple[typing.List[T_co]], '(+T_co,)'),
    (MyGeneric, '(~E,)'),
])
def test_get_type_parameters(type_, expected):
    params = get_type_parameters(type_)
    assert str(params) == expected


@pytest.mark.parametrize('type_', [
    3,
    ...,
])
def test_get_type_parameters_typeerror(type_):
    with pytest.raises(TypeError):
        get_type_parameters(type_)


@pytest.mark.parametrize('type_', [
    None,
    'List',
    UnhashableClass,
    typing.Any,
    typing.Generic,
    Protocol,
])
def test_get_type_parameters_valueerror(type_):
    with pytest.raises(ValueError):
        get_type_parameters(type_)


if is_py39_plus:
    @pytest.mark.parametrize('type_, expected', [
        (list, '(~T,)'),
        (collections.abc.Callable, '(-A_contra, +R_co)'),
        (tuple, '(+T_co,)'),
        (type, '(+CT_co,)'),
        (collections.abc.ByteString, '()'),
        (list[E], '(~E,)'),
        (list[int], '()'),
        (collections.abc.Generator[E, int, E], '(~E,)'),
        (tuple[E, int, T_co], '(~E, +T_co)'),
        (collections.abc.Callable[[E, int], E][T_co], '(+T_co,)'),
        (tuple[list[T_co]], '(+T_co,)'),
    ])
    def test_get_type_parameters_py39(type_, expected):
        params = get_type_parameters(type_)
        assert str(params) == expected


@pytest.mark.parametrize('type_, expected', [
    (int, 'int'),
    (None, 'NoneType'),
    (type(None), 'NoneType'),
    (type(...), 'ellipsis'),
    (UnhashableClass, 'UnhashableClass'),
    (MyGeneric, 'MyGeneric'),
    (typing.Any, 'Any'),
    (typing.List, 'List'),
    (typing.Tuple, 'Tuple'),
    (typing.Union, 'Union'),
    (typing.Optional, 'Optional'),
    (typing.Callable, 'Callable'),
    (typing.TypeVar, 'TypeVar'),
    (typing.Generic, 'Generic'),
])
def test_get_type_name(type_, expected):
    assert get_type_name(type_) == expected


@pytest.mark.parametrize('type_', [
    3,
    'List',
    typing.List[int],
    typing.Tuple[int, str],
    typing.Optional[str],
    typing.Union[int, float],
    typing.Callable[..., None],
])
def test_get_type_name_error(type_):
    with pytest.raises(TypeError):
        get_type_name(type_)


# === Literal ===
if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, True),
    ])
    def test_literal_is_variadic_generic(type_, expected):
        assert is_variadic_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, False),
        (typing.Literal[1, 2], True),
    ])
    def test_literal_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, True),
        (typing.Literal[1, 2], False),
        (typing.Literal[1, E], False),
    ])
    def test_literal_is_generic_base_class(type_, expected):
        assert is_generic_base_class(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, True),
        (typing.Literal[1, 2], False),
    ])
    def test_literal_is_generic(type_, expected):
        assert is_generic(type_) == expected


    @pytest.mark.parametrize('type_', [
        typing.Literal,
    ])
    def test_get_literal_params_error(type_):
        with pytest.raises(ValueError):
            get_type_parameters(type_)


# === Protocol ===
if hasattr(typing, 'Protocol'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Protocol, True),
    ])
    def test_protocol_is_type(type_, expected):
        assert is_type(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Protocol, False),
    ])
    def test_protocol_is_generic(type_, expected):
        assert is_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Protocol, False),
    ])
    def test_protocol_is_parameterized_generic(type_, expected):
        assert is_parameterized_generic(type_) == expected


    @pytest.mark.parametrize('type_', [
        typing.Protocol,
    ])
    def test_get_protocol_params_error(type_):
        with pytest.raises(ValueError):
            get_type_parameters(type_)


    def test_get_protocol_name():
        assert get_type_name(typing.Protocol) == 'Protocol'


# === ClassVar ===
if hasattr(typing, 'ClassVar'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.ClassVar, False),
        (typing.ClassVar[str], True),
        (typing.ClassVar[E], sys.version_info < (3, 7)),
    ])
    def test_classvar_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.ClassVar, True),
        (typing.ClassVar[int], False),
        (typing.ClassVar[E], False),
    ])
    def test_classvar_is_generic_base_class(type_, expected):
        assert is_generic_base_class(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.ClassVar, True),
        (typing.ClassVar[str], False),
        (typing.ClassVar[E], sys.version_info >= (3, 7)),
    ])
    def test_classvar_is_generic(type_, expected):
        assert is_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.ClassVar, '(+T_co,)'),
        (typing.ClassVar[int], '()'),
        (typing.ClassVar[E], '(~E,)' if sys.version_info >= (3, 7) else '()'),
    ])
    def test_get_classvar_params(type_, expected):
        params = get_type_parameters(type_)
        assert str(params) == expected
    
    
    @pytest.mark.parametrize('type_, expected', [
        (typing.ClassVar, 'ClassVar'),
    ])
    def test_get_classvar_name(type_, expected):
        assert get_type_name(type_) == expected


# === Final ===
if hasattr(typing, 'Final'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Final, False),
        (typing.Final[str], True),
        (typing.Final[E], False),
    ])
    def test_final_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Final, True),
        (typing.Final[int], False),
        (typing.Final[E], False),
    ])
    def test_final_is_generic_base_class(type_, expected):
        assert is_generic_base_class(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Final, True),
        (typing.Final[str], False),
        (typing.Final[E], True),
    ])
    def test_final_is_generic(type_, expected):
        assert is_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Final, '(+T_co,)'),
    ])
    def test_get_final_params(type_, expected):
        params = get_type_parameters(type_)
        assert str(params) == expected


# === Annotated ===
if hasattr(typing, 'Annotated'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Annotated, False),
        (typing.Annotated[str, 'idk lol'], True),
        (typing.Annotated[E, 'foobar'], False),
    ])
    def test_annotated_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Annotated, True),
        (typing.Annotated[int, 5], False),
        (typing.Annotated[E, 5], False),
    ])
    def test_annotated_is_generic_base_class(type_, expected):
        assert is_generic_base_class(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Annotated, True),
        (typing.Annotated[str, ''], False),
        (typing.Annotated[E, None], True),
    ])
    def test_annotated_is_generic(type_, expected):
        assert is_generic(type_) == expected


    @pytest.mark.parametrize('type_, expected', [
        (typing.Annotated, '(+T_co,)'),
    ])
    def test_get_annotated_params(type_, expected):
        params = get_type_parameters(type_)
        assert str(params) == expected

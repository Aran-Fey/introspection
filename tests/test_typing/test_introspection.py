import pytest

import collections.abc
import re
import sys
import types
import typing
import typing_extensions

from introspection.typing import *
from introspection import errors


is_py39_plus = sys.version_info >= (3, 9)


T = typing.TypeVar("T")
T_co = typing.TypeVar("T_co", covariant=True)
E = typing.TypeVar("E", bound=Exception)


class MyGeneric(typing.Generic[E]):
    pass


class UnhashableMeta(type):
    __hash__ = None


class UnhashableClass(metaclass=UnhashableMeta):
    pass


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (list, False),
        (None, False),
        (UnhashableClass, False),
        (typing.List, False),
        ("Foo", True),
        (typing.ForwardRef("Foo"), True),
    ],
)
def test_is_forwardref(type_, expected):
    assert is_forwardref(type_) == expected


@pytest.mark.parametrize(
    "obj",
    [
        3,
        ...,
    ],
)
def test_is_forwardref_error(obj):
    with pytest.raises(errors.NotAType):
        is_forwardref(obj)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_forwardref(obj)


@pytest.mark.parametrize(
    "obj",
    [
        3,
        ...,
    ],
)
def test_is_forwardref_non_raising(obj):
    assert not is_forwardref(obj, raising=False)


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, True),
        (list, True),
        (UnhashableClass, True),
        (None, True),
        (..., False),
        (3, False),
        ([], False),
        ("Foo", True),  # this is a forward reference
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
        (typing_extensions.Protocol, True),
    ],
)
def test_is_type(type_, expected):
    assert is_type(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        ("Foo", False),
        (typing.ForwardRef("Foo"), False),
    ],
)
def test_is_type_no_forwardref(type_, expected):
    assert is_type(type_, allow_forwardref=False) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (list, False),
        (UnhashableClass, False),
        (None, False),
        ("List", False),
        (typing.ForwardRef("List"), False),
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
    ],
)
def test_is_typing_type(type_, expected):
    assert is_typing_type(type_, raising=True) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_typing_type_error(type_):
    with pytest.raises(errors.NotAType):
        is_typing_type(type_, raising=True)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_typing_type(type_, raising=True)


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_typing_type_non_raising(type_):
    assert not is_typing_type(type_, raising=False)


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (None, False),
        ("List", False),
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
        (typing.Generic, True),
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
        (typing_extensions.Protocol, True),
        (typing_extensions.Literal, True),
        (typing_extensions.Literal[1, 2], False),
        (typing_extensions.ClassVar, True),
        (typing_extensions.ClassVar[str], False),
        (typing_extensions.ClassVar[E], sys.version_info >= (3, 7)),
        (typing_extensions.Final, True),
        (typing_extensions.Final[str], False),
        (typing_extensions.Final[E], True),
        (typing_extensions.Annotated, True),
        (typing_extensions.Annotated[str, ""], False),
        (typing_extensions.Annotated[E, None], True),
    ],
)
def test_is_generic(type_, expected):
    assert is_generic(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_generic_error(type_):
    with pytest.raises(errors.NotAType):
        is_generic(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_generic(type_)


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_generic_non_raising(type_):
    assert not is_generic(type_, raising=False)


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (list, False),
        (tuple, is_py39_plus),
        (UnhashableClass, False),
        (collections.abc.Callable, False),
        (None, False),
        ("List", False),
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
        (typing_extensions.Literal, True),
        (typing_extensions.Literal[3], False),
    ],
)
def test_is_variadic_generic(type_, expected):
    assert is_variadic_generic(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_variadic_generic_error(type_):
    with pytest.raises(errors.NotAType):
        is_variadic_generic(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_variadic_generic(type_)


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_variadic_generic_non_raising(type_):
    assert not is_variadic_generic(type_, raising=False)


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (list, is_py39_plus),
        (tuple, is_py39_plus),
        (UnhashableClass, False),
        (None, False),
        ("List", False),
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
        (typing_extensions.Literal, True),
        (typing_extensions.Literal[1, 2], False),
        (typing_extensions.Literal[1, E], False),
        (typing_extensions.ClassVar, True),
        (typing_extensions.ClassVar[int], False),
        (typing_extensions.ClassVar[E], False),
        (typing_extensions.Final, True),
        (typing_extensions.Final[int], False),
        (typing_extensions.Final[E], False),
        (typing_extensions.Annotated, True),
        (typing_extensions.Annotated[int, 5], False),
        (typing_extensions.Annotated[E, 5], False),
    ],
)
def test_is_generic_base_class(type_, expected):
    assert is_generic_base_class(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_generic_base_class_error(type_):
    with pytest.raises(errors.NotAType):
        is_generic_base_class(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_generic_base_class(type_)


@pytest.mark.parametrize(
    ["type_", "expected"],
    [
        (int, False),
        (list, False),
        (UnhashableClass, False),
        (None, False),
        ("List", False),
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
        (typing_extensions.Literal, False),
        (typing_extensions.Literal[3], True),
        (typing_extensions.Protocol, False),
        (typing_extensions.Protocol[E], True),
    ],
)
def test_is_parameterized_generic(type_, expected):
    assert is_parameterized_generic(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_parameterized_generic_error(type_):
    with pytest.raises(errors.NotAType):
        is_parameterized_generic(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_parameterized_generic(type_)


if is_py39_plus:

    @pytest.mark.parametrize(
        ["type_", "expected"],
        [
            (type[str], True),
            (list[int], True),
            (re.Pattern[str], True),
            (re.Match[bytes], True),
            (collections.Counter[str], True),
            (collections.defaultdict[int, E], True),
            (list[E], True),
            (list[tuple[E]], True),
        ],
    )
    def test_is_parameterized_generic_py39(type_, expected):
        assert is_parameterized_generic(type_) == expected


@pytest.mark.parametrize(
    ["type_", "expected"],
    [
        (int, False),
        (list, False),
        (UnhashableClass, False),
        (None, False),
        ("List", False),
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
        (typing_extensions.Literal, False),
        (typing_extensions.Literal[1, 2], True),
        (typing_extensions.Protocol, False),
        (typing_extensions.Final, False),
        (typing_extensions.Final[str], True),
        (typing_extensions.Final[E], False),
        (typing_extensions.ClassVar, False),
        (typing_extensions.ClassVar[str], True),
        (typing_extensions.ClassVar[E], sys.version_info < (3, 7)),
        (typing_extensions.Annotated, False),
        (typing_extensions.Annotated[str, "idk lol"], True),
        (typing_extensions.Annotated[E, "foobar"], False),
    ],
)
def test_is_fully_parameterized_generic(type_, expected):
    assert is_fully_parameterized_generic(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_fully_parameterized_generic_error(type_):
    with pytest.raises(errors.NotAType):
        is_fully_parameterized_generic(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        is_fully_parameterized_generic(type_)


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_is_fully_parameterized_generic_non_raising(type_):
    assert not is_fully_parameterized_generic(type_, raising=False)


if is_py39_plus:

    @pytest.mark.parametrize(
        ["type_", "expected"],
        [
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
        ],
    )
    def test_is_fully_parameterized_generic_py39(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (typing.List[int], typing.List),
        (typing.List[E], typing.List),
        (typing.Union[int, str], typing.Union),
        (typing.Callable[[], int], typing.Callable),
        (typing.Optional[int], typing.Optional),
    ],
)
def test_get_generic_base_class(type_, expected):
    assert get_generic_base_class(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_get_generic_base_class_typeerror(type_):
    with pytest.raises(errors.NotAType):
        get_generic_base_class(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        get_generic_base_class(type_)


@pytest.mark.parametrize(
    "type_",
    [
        None,
        "List",
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
    ],
)
def test_get_generic_base_class_valueerror(type_):
    with pytest.raises(errors.NotAParameterizedGeneric):
        get_generic_base_class(type_)

    # Deprecated exception
    with pytest.raises(ValueError):
        get_generic_base_class(type_)


if is_py39_plus:

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (list[int], list),
            (list[E], list),
            (tuple[list[str]], tuple),
            (re.Pattern[str], re.Pattern),
            (re.Match[bytes], re.Match),
            (collections.deque[int], collections.deque),
            (collections.abc.Iterator[str], collections.abc.Iterator),
        ],
    )
    def test_get_generic_base_class_py39(type_, expected):
        assert get_generic_base_class(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
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
        (
            typing.Tuple[typing.List[typing.Type[E]]][str],
            (typing.List[typing.Type[str]],),
        ),
    ],
)
def test_get_type_arguments(type_, expected):
    assert get_type_arguments(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_get_type_arguments_typeerror(type_):
    with pytest.raises(errors.NotAType):
        get_type_arguments(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        get_type_arguments(type_)


@pytest.mark.parametrize(
    "type_",
    [
        None,
        "List",
        typing.List,
        typing.Tuple,
        typing.Optional,
        typing.Union,
        typing.Callable,
        typing.Type,
    ],
)
def test_get_type_arguments_valueerror(type_):
    with pytest.raises(errors.NotAParameterizedGeneric):
        get_type_arguments(type_)

    # Deprecated exception
    with pytest.raises(ValueError):
        get_type_arguments(type_)


if is_py39_plus:

    @pytest.mark.parametrize(
        "type_, expected",
        [
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
        ],
    )
    def test_get_type_arguments_py39(type_, expected):
        assert get_type_arguments(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (typing.List, "(~T,)"),
        (typing.Union, "(+T_co,)"),
        (typing.Callable, "(-A_contra, +R_co)"),
        (typing.Optional, "(+T_co,)"),
        (typing.Tuple, "(+T_co,)"),
        (typing.Type, "(+CT_co,)"),
        (typing.ByteString, "()"),
        (typing.List[E], "(~E,)"),
        (typing.List[int], "()"),
        (typing.Generator[E, int, E], "(~E,)"),
        (typing.Tuple[E, int, T_co], "(~E, +T_co)"),
        (typing.Callable[[E, int], E][T_co], "(+T_co,)"),
        (typing.Tuple[typing.List[T_co]], "(+T_co,)"),
        (MyGeneric, "(~E,)"),
        (typing_extensions.Protocol[E], "(~E,)"),
        (typing_extensions.ClassVar, "(+T_co,)"),
        (typing_extensions.ClassVar[int], "()"),
        (
            typing_extensions.ClassVar[E],
            "(~E,)" if sys.version_info >= (3, 7) else "()",
        ),
        (typing_extensions.Final, "(+T_co,)"),
        (typing_extensions.Annotated, "(+T_co,)"),
    ],
)
def test_get_type_parameters(type_, expected):
    params = get_type_parameters(type_)
    assert str(params) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        ...,
    ],
)
def test_get_type_parameters_typeerror(type_):
    with pytest.raises(errors.NotAType):
        get_type_parameters(type_)

    # Deprecated exception
    with pytest.raises(TypeError):
        get_type_parameters(type_)


@pytest.mark.parametrize(
    "type_",
    [
        None,
        "List",
        typing.Any,
        typing.Generic,
        typing_extensions.Protocol,
        typing_extensions.Literal,
    ],
)
def test_get_type_parameters_valueerror(type_):
    with pytest.raises(errors.NotAGeneric):
        get_type_parameters(type_)

    # Deprecated exception
    with pytest.raises(ValueError):
        get_type_parameters(type_)


if is_py39_plus:

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (list, "(~T,)"),
            (collections.abc.Callable, "(-A_contra, +R_co)"),
            (tuple, "(+T_co,)"),
            (type, "(+CT_co,)"),
            (collections.abc.ByteString, "()"),
            (list[E], "(~E,)"),
            (list[int], "()"),
            (collections.abc.Generator[E, int, E], "(~E,)"),
            (tuple[E, int, T_co], "(~E, +T_co)"),
            (collections.abc.Callable[[E, int], E][T_co], "(+T_co,)"),
            (tuple[list[T_co]], "(+T_co,)"),
        ],
    )
    def test_get_type_parameters_py39(type_, expected):
        params = get_type_parameters(type_)
        assert str(params) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, "int"),
        (None, "NoneType"),
        (type(None), "NoneType"),
        (type(...), "ellipsis"),
        (UnhashableClass, "UnhashableClass"),
        (MyGeneric, "MyGeneric"),
        (typing.Any, "Any"),
        (typing.List, "List"),
        (typing.Tuple, "Tuple"),
        (typing.Union, "Union"),
        (typing.Optional, "Optional"),
        (typing.Callable, "Callable"),
        (typing.TypeVar, "TypeVar"),
        (typing.Generic, "Generic"),
        (typing_extensions.Literal, "Literal"),
        (typing_extensions.Protocol, "Protocol"),
        (typing_extensions.ClassVar, "ClassVar"),
    ],
)
def test_get_type_name(type_, expected):
    assert get_type_name(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        "List",
        typing.List[int],
        typing.Tuple[int, str],
        typing.Optional[str],
        typing.Union[int, float],
        typing.Callable[..., None],
    ],
)
def test_get_type_name_error(type_):
    with pytest.raises(errors.Error):
        get_type_name(type_)


# === new Union syntax ===
if sys.version_info >= (3, 10):

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, True),
            (str | None, True),
            (str | int, True),
            (str | T, True),
            ((str | T)[int], True),
        ],
    )
    def test_uniontype_is_type(type_, expected):
        assert is_type(type_) == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, True),
            (str | None, True),
            (str | int, True),
            (str | T, True),
            ((str | T)[int], True),
        ],
    )
    def test_uniontype_is_typing_type(type_, expected):
        assert is_typing_type(type_, raising=True) == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, False),
            (str | None, False),
            (str | int, False),
            (str | T, True),
            (E | T | str, True),
            ((str | T)[int], False),
        ],
    )
    def test_uniontype_is_generic(type_, expected):
        assert is_generic(type_) == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, False),
            (str | None, False),
            (str | int, False),
            (str | T, False),
            (E | T | str, False),
            ((str | T)[int], False),
        ],
    )
    def test_uniontype_is_variadic_generic(type_, expected):
        assert is_variadic_generic(type_) == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, False),
            (str | None, True),
            (str | int, True),
            (str | T, True),
            (E | T | str, True),
            ((str | T)[int], True),
        ],
    )
    def test_uniontype_is_parameterized_generic(type_, expected):
        assert is_parameterized_generic(type_) == expected

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (types.UnionType, False),
            (str | None, True),
            (str | int, True),
            (str | T, False),
            (E | T | str, False),
            ((str | T)[float], True),
        ],
    )
    def test_uniontype_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected

    @pytest.mark.parametrize(
        "type_",
        [
            str | int,
            str | T,
            E | T | str,
            (str | T)[int],
        ],
    )
    def test_uniontype_get_generic_base_class(type_):
        assert get_generic_base_class(type_) is typing.Union

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (
                str | None,
                (str,),
            ),  # No None in the output since this is seen as an Optional[str]
            (str | float, (str, float)),
            (str | T, (str, T)),
            (E | T | str, (E, T, str)),
            ((str | T)[int], (str, int)),
        ],
    )
    def test_uniontype_get_type_arguments(type_, expected):
        assert get_type_arguments(type_) == expected

    def test_uniontype_get_type_arguments_error():
        with pytest.raises(errors.NotAParameterizedGeneric):
            get_type_arguments(types.UnionType)

        # Deprecated exception
        with pytest.raises(ValueError):
            get_type_arguments(types.UnionType)

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (str | None, ()),
            (str | int, ()),
            (str | T, (T,)),
            (E | T | str, (E, T)),
            ((str | T)[float], ()),
        ],
    )
    def test_uniontype_get_type_parameters(type_, expected):
        assert get_type_parameters(type_) == expected

    def test_uniontype_get_type_parameters_error():
        with pytest.raises(errors.NotAGeneric):
            get_type_parameters(types.UnionType)

        # Deprecated exception
        with pytest.raises(ValueError):
            get_type_parameters(types.UnionType)

import pytest

import collections.abc
import re
import sys
import types
import typing
import typing_extensions
from typing import *

from introspection.typing import *
from introspection import errors
from introspection.types import Type_

from typing import Type  # overwrite the `Type` imported from `introspection.typing`


is_py39_plus = sys.version_info >= (3, 9)


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
E = TypeVar("E", bound=Exception)


class MyGeneric(Generic[E]):
    pass


class UnhashableMeta(type):
    __hash__ = None  # type: ignore


class UnhashableClass(metaclass=UnhashableMeta):
    pass


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, False),
        (list, False),
        (None, False),
        (UnhashableClass, False),
        (List, False),
        ("Foo", True),
        (ForwardRef("Foo"), True),
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
        (Any, True),
        (List, True),
        (Union, True),
        (Callable, True),
        (Optional, True),
        (Type, True),
        (NoReturn, True),
        (MyGeneric, True),
        (TypeVar, True),
        (List[int], True),
        (Union[int, str], True),
        (Callable[[], int], True),
        (Optional[int], True),
        (ByteString, True),
        (List[E], True),  # type: ignore
        (MyGeneric[E], True),  # type: ignore
        (MyGeneric[int], True),  # type: ignore
        (List[Tuple[E]], True),  # type: ignore
        (List[Tuple], True),
        (List[Callable[[E], int]], True),  # type: ignore
        (List[Callable], True),
        (typing_extensions.Protocol, True),
        (typing_extensions.Literal, True),
    ],
)
def test_is_type(type_, expected):
    assert is_type(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        ("Foo", False),
        (ForwardRef("Foo"), False),
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
        (ForwardRef("List"), False),
        (T_co, True),
        (E, True),
        (Any, True),
        (List, True),
        (Union, True),
        (Callable, True),
        (Optional, True),
        (Type, True),
        (NoReturn, True),
        (MyGeneric, False),
        (TypeVar, True),
        (List[int], True),
        (Union[int, str], True),
        (Callable[[], int], True),
        (Optional[int], True),
        (ByteString, True),
        (List[E], True),  # type: ignore
        (MyGeneric[E], True),  # type: ignore
        (MyGeneric[int], True),  # type: ignore
        (List[Tuple[E]], True),  # type: ignore
        (List[Tuple], True),
        (List[Callable[[E], int]], True),  # type: ignore
        (List[Callable], True),
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
        (Any, False),
        (List, True),
        (Union, True),
        (Tuple, True),
        (Callable, True),
        (Optional, True),
        (Type, True),
        (Generic, True),
        (MyGeneric, True),
        (List[int], False),
        (Union[int, str], False),
        (Tuple[int], False),
        (Callable[[], int], False),
        (Optional[int], False),
        (ByteString, False),
        (List[E], True),  # type: ignore
        (Tuple[E], True),  # type: ignore
        (MyGeneric[E], True),  # type: ignore
        (MyGeneric[int], False),  # type: ignore
        (List[Tuple[E]], True),  # type: ignore
        (List[Tuple], False),
        (List[Callable[[E], int]], True),  # type: ignore
        (List[Callable], False),
        (typing_extensions.Protocol, True),
        (typing_extensions.Literal, True),
        (typing_extensions.Literal[1, 2], False),
        (typing_extensions.ClassVar, True),
        (typing_extensions.ClassVar[str], False),
        (typing_extensions.ClassVar[E], sys.version_info >= (3, 7)),  # type: ignore
        (typing_extensions.Final, True),
        (typing_extensions.Final[str], False),
        (typing_extensions.Final[E], True),  # type: ignore
        (typing_extensions.Annotated, True),
        (typing_extensions.Annotated[str, ""], False),
        (typing_extensions.Annotated[E, None], True),  # type: ignore
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
        (Any, False),
        (Union, True),
        (Tuple, True),
        (List, False),
        (Callable, False),
        (Optional, False),
        (Type, False),
        (MyGeneric, False),
        (List[int], False),
        (Union[int, str], False),
        (Tuple[int], False),
        (Callable[[], int], False),
        (Optional[int], False),
        (ByteString, False),
        (List[E], False),  # type: ignore
        (Tuple[E], False),  # type: ignore
        (MyGeneric[E], False),  # type: ignore
        (MyGeneric[int], False),  # type: ignore
        (List[Tuple[E]], False),  # type: ignore
        (List[Tuple], False),
        (List[Callable[[E], int]], False),  # type: ignore
        (List[Callable], False),
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
        (Any, False),
        (List, True),
        (Union, True),
        (Callable, True),
        (Optional, True),
        (Type, True),
        (MyGeneric, True),
        (List[int], False),
        (Union[int, str], False),
        (Callable[[], int], False),
        (Optional[int], False),
        (ByteString, False),
        (List[E], False),  # type: ignore
        (MyGeneric[E], False),  # type: ignore
        (typing_extensions.Literal, True),
        (typing_extensions.Literal[1, 2], False),
        (typing_extensions.Literal[1, E], False),  # type: ignore
        (typing_extensions.ClassVar, True),
        (typing_extensions.ClassVar[int], False),
        (typing_extensions.ClassVar[E], False),  # type: ignore
        (typing_extensions.Final, True),
        (typing_extensions.Final[int], False),
        (typing_extensions.Final[E], False),  # type: ignore
        (typing_extensions.Annotated, True),
        (typing_extensions.Annotated[int, 5], False),
        (typing_extensions.Annotated[E, 5], False),  # type: ignore
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
        (Any, False),
        (List, False),
        (Union, False),
        (Callable, False),
        (Optional, False),
        (Type, False),
        (MyGeneric, False),
        (Type[str], True),
        (List[int], True),
        (Union[int, str], True),
        (Callable[[], int], True),
        (Optional[int], True),
        (MyGeneric[str], True),  # type: ignore
        (MyGeneric[E], True),  # type: ignore
        (List[E], True),  # type: ignore
        (List[Tuple[E]], True),  # type: ignore
        (typing_extensions.Literal, False),
        (typing_extensions.Literal[3], True),
        (typing_extensions.Protocol, False),
        (typing_extensions.Protocol[E], True),  # type: ignore
    ],
)
def test_is_parameterized_generic(type_, expected):
    assert is_parameterized_generic(type_) == expected


if hasattr(typing, "Literal"):

    @pytest.mark.parametrize(
        ["type_", "expected"],
        [
            (typing.Literal, False),
            (typing.Literal[3], True),
        ],
    )
    def test_literal_is_parameterized_generic(type_, expected):
        assert is_parameterized_generic(type_) == expected


if hasattr(typing, "Protocol"):

    @pytest.mark.parametrize(
        ["type_", "expected"],
        [
            (typing.Protocol, False),
            (typing.Protocol[E], True),  # type: ignore
        ],
    )
    def test_protocol_is_parameterized_generic(type_, expected):
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
            (collections.defaultdict[int, E], True),  # type: ignore
            (list[E], True),  # type: ignore
            (list[tuple[E]], True),  # type: ignore
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
        (Any, False),
        (List, False),
        (Union, False),
        (Callable, False),
        (Optional, False),
        (ByteString, True),
        (MyGeneric, False),
        (Type[int], True),
        (List[int], True),
        (Union[int, str], True),
        (Callable[[], int], True),
        (Optional[int], True),
        (MyGeneric[str], True),  # type: ignore
        (List[E], False),  # type: ignore
        (List[List[E]], False),  # type: ignore
        (typing_extensions.Literal, False),
        (typing_extensions.Literal[1, 2], True),
        (typing_extensions.Protocol, False),
        (typing_extensions.Final, False),
        (typing_extensions.Final[str], True),
        (typing_extensions.Final[E], False),  # type: ignore
        (typing_extensions.ClassVar, False),
        (typing_extensions.ClassVar[str], True),
        (typing_extensions.ClassVar[E], sys.version_info < (3, 7)),  # type: ignore
        (typing_extensions.Annotated, False),
        (typing_extensions.Annotated[str, "idk lol"], True),
        (typing_extensions.Annotated[E, "foobar"], False),  # type: ignore
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
            (tuple[E], False),  # type: ignore
            (list[E], False),  # type: ignore
            (list[tuple[E]], False),  # type: ignore
            (tuple[list[int]], True),
            (tuple[list[E]], False),  # type: ignore
            (re.Pattern[str], True),
            (re.Match[bytes], True),
            (collections.Counter[str], True),
            (collections.defaultdict[int, E], False),  # type: ignore
            (collections.abc.Iterable[str], True),
            (collections.abc.Iterable[E], False),  # type: ignore
        ],
    )
    def test_is_fully_parameterized_generic_py39(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (List[int], List),
        (List[E], List),  # type: ignore
        (Union[int, str], Union),
        (Callable[[], int], Callable),
        (Optional[int], Optional),
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
        List,
        Tuple,
        Optional,
        Union,
        Callable,
        Type,
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
            (list[E], list),  # type: ignore
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
        (List[int], (int,)),
        (Union[int, str], (int, str)),
        (Callable[[], int], ([], int)),
        (Callable[[str], int], ([str], int)),
        (Callable[..., int], (..., int)),
        (Optional[int], (int,)),
        (Type[str], (str,)),
        (List[E], (E,)),  # type: ignore
        (Generator[E, int, E][str], (str, int, str)),  # type: ignore
        (Tuple[E, int, E][str], (str, int, str)),  # type: ignore
        (Callable[[E, int], E][str], ([str, int], str)),  # type: ignore
        (Tuple[List[E]][str], (List[str],)),  # type: ignore
        (
            Tuple[List[Type[E]]][str],  # type: ignore
            (List[Type[str]],),
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
        List,
        Tuple,
        Optional,
        Union,
        Callable,
        Type,
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
            (list[E], (E,)),  # type: ignore
            (collections.abc.Generator[E, int, E][str], (str, int, str)),  # type: ignore
            (tuple[E, int, E][str], (str, int, str)),  # type: ignore
            (collections.abc.Callable[[E, int], E][str], ([str, int], str)),  # type: ignore
            (tuple[list[E]][str], (list[str],)),  # type: ignore
            (tuple[list[type[E]]][str], (list[type[str]],)),  # type: ignore
        ],
    )
    def test_get_type_arguments_py39(type_, expected):
        assert get_type_arguments(type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (List, "(~T,)"),
        (Union, "(+T_co,)"),
        (Callable, "(-A_contra, +R_co)"),
        (Optional, "(+T_co,)"),
        (Tuple, "(+T_co,)"),
        (Type, "(+CT_co,)"),
        (ByteString, "()"),
        (List[E], "(~E,)"),  # type: ignore
        (List[int], "()"),
        (Generator[E, int, E], "(~E,)"),  # type: ignore
        (Tuple[E, int, T_co], "(~E, +T_co)"),  # type: ignore
        (Callable[[E, int], E][T_co], "(+T_co,)"),  # type: ignore
        (Tuple[List[T_co]], "(+T_co,)"),  # type: ignore
        (MyGeneric, "(~E,)"),
        (typing_extensions.Protocol[E], "(~E,)"),  # type: ignore
        (typing_extensions.ClassVar, "(+T_co,)"),
        (typing_extensions.ClassVar[int], "()"),
        (
            typing_extensions.ClassVar[E],  # type: ignore
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
        Any,
        Generic,
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
            (list[E], "(~E,)"),  # type: ignore
            (list[int], "()"),
            (collections.abc.Generator[E, int, E], "(~E,)"),  # type: ignore
            (tuple[E, int, T_co], "(~E, +T_co)"),  # type: ignore
            (collections.abc.Callable[[E, int], E][T_co], "(+T_co,)"),  # type: ignore
            (tuple[list[T_co]], "(+T_co,)"),  # type: ignore
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
        (type(None), "NoneType"),  # type: ignore
        (type(...), "ellipsis"),  # type: ignore
        (UnhashableClass, "UnhashableClass"),
        (MyGeneric, "MyGeneric"),
        (Any, "Any"),
        (List, "List"),
        (Tuple, "Tuple"),
        (Union, "Union"),
        (Optional, "Optional"),
        (Callable, "Callable"),
        (TypeVar, "TypeVar"),
        (Generic, "Generic"),
        (typing_extensions.Literal, "Literal"),
        (typing_extensions.Protocol, "Protocol"),
        (typing_extensions.ClassVar, "ClassVar"),
        (typing_extensions.ParamSpec, "ParamSpec"),
        (typing_extensions.Final, "Final"),
    ],
)
def test_get_type_name(type_, expected):
    assert get_type_name(type_) == expected


@pytest.mark.parametrize(
    "type_",
    [
        3,
        "List",
        List[int],
        Tuple[int, str],
        Optional[str],
        Union[int, float],
        Callable[..., None],
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
            (str | T, True),  # type: ignore
            ((str | T)[int], True),  # type: ignore
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
            (str | T, True),  # type: ignore
            ((str | T)[int], True),  # type: ignore
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
            (str | T, True),  # type: ignore
            (E | T | str, True),  # type: ignore
            ((str | T)[int], False),  # type: ignore
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
            (str | T, False),  # type: ignore
            (E | T | str, False),  # type: ignore
            ((str | T)[int], False),  # type: ignore
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
            (str | T, True),  # type: ignore
            (E | T | str, True),  # type: ignore
            ((str | T)[int], True),  # type: ignore
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
            (str | T, False),  # type: ignore
            (E | T | str, False),  # type: ignore
            ((str | T)[float], True),  # type: ignore
        ],
    )
    def test_uniontype_is_fully_parameterized_generic(type_, expected):
        assert is_fully_parameterized_generic(type_) == expected

    @pytest.mark.parametrize(
        "type_",
        [
            str | int,
            str | T,  # type: ignore
            E | T | str,  # type: ignore
            (str | T)[int],  # type: ignore
        ],
    )
    def test_uniontype_get_generic_base_class(type_):
        assert get_generic_base_class(type_) is Union

    @pytest.mark.parametrize(
        "type_, expected",
        [
            (
                str | None,
                (str,),
            ),  # No None in the output since this is seen as an Optional[str]
            (str | float, (str, float)),
            (str | T, (str, T)),  # type: ignore
            (E | T | str, (E, T, str)),  # type: ignore
            ((str | T)[int], (str, int)),  # type: ignore
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
            (str | T, (T,)),  # type: ignore
            (E | T | str, (E, T)),  # type: ignore
            ((str | T)[float], ()),  # type: ignore
        ],
    )
    def test_uniontype_get_type_parameters(type_: Type_, expected: Tuple[TypeVar]):
        assert get_type_parameters(type_) == expected

    def test_uniontype_get_type_parameters_error():
        with pytest.raises(errors.NotAGeneric):
            get_type_parameters(types.UnionType)

        # Deprecated exception
        with pytest.raises(ValueError):
            get_type_parameters(types.UnionType)

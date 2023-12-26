import pytest

import collections.abc
import re
import sys
import types
import typing_extensions
from typing import *  # type: ignore

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
        (List[E], True),
        (MyGeneric[E], True),
        (MyGeneric[int], True),
        (List[Tuple[E]], True),
        (List[Tuple], True),
        (List[Callable[[E], int]], True),
        (List[Callable], True),
        (typing_extensions.Protocol, True),
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
        (List[E], True),
        (MyGeneric[E], True),
        (MyGeneric[int], True),
        (List[Tuple[E]], True),
        (List[Tuple], True),
        (List[Callable[[E], int]], True),
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
        (List[E], True),
        (Tuple[E], True),
        (MyGeneric[E], True),
        (MyGeneric[int], False),
        (List[Tuple[E]], True),
        (List[Tuple], False),
        (List[Callable[[E], int]], True),
        (List[Callable], False),
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
        (List[E], False),
        (Tuple[E], False),
        (MyGeneric[E], False),
        (MyGeneric[int], False),
        (List[Tuple[E]], False),
        (List[Tuple], False),
        (List[Callable[[E], int]], False),
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
        (List[E], False),
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
        (MyGeneric[str], True),
        (MyGeneric[E], True),
        (List[E], True),
        (List[Tuple[E]], True),
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
        (MyGeneric[str], True),
        (List[E], False),
        (List[List[E]], False),
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
        (List[int], List),
        (List[E], List),
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
        (List[int], (int,)),
        (Union[int, str], (int, str)),
        (Callable[[], int], ([], int)),
        (Callable[[str], int], ([str], int)),
        (Callable[..., int], (..., int)),
        (Optional[int], (int,)),
        (Type[str], (str,)),
        (List[E], (E,)),
        (Generator[E, int, E][str], (str, int, str)),
        (Tuple[E, int, E][str], (str, int, str)),
        (Callable[[E, int], E][str], ([str, int], str)),
        (Tuple[List[E]][str], (List[str],)),
        (
            Tuple[List[Type[E]]][str],
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
        (List, "(~T,)"),
        (Union, "(+T_co,)"),
        (Callable, "(-A_contra, +R_co)"),
        (Optional, "(+T_co,)"),
        (Tuple, "(+T_co,)"),
        (Type, "(+CT_co,)"),
        (ByteString, "()"),
        (List[E], "(~E,)"),
        (List[int], "()"),
        (Generator[E, int, E], "(~E,)"),
        (Tuple[E, int, T_co], "(~E, +T_co)"),
        (Callable[[E, int], E][T_co], "(+T_co,)"),
        (Tuple[List[T_co]], "(+T_co,)"),
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
        assert get_generic_base_class(type_) is Union

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
    def test_uniontype_get_type_parameters(type_: Type_, expected: Tuple[TypeVar]):
        assert get_type_parameters(type_) == expected

    def test_uniontype_get_type_parameters_error():
        with pytest.raises(errors.NotAGeneric):
            get_type_parameters(types.UnionType)

        # Deprecated exception
        with pytest.raises(ValueError):
            get_type_parameters(types.UnionType)

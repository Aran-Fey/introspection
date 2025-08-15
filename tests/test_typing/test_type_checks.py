import pytest

import sys
import typing as t

from introspection.typing import is_instance, is_subtype


T = t.TypeVar("T")


class AwaitableObject:
    def __await__(self) -> t.Iterator[None]: ...


def func_with_forwardrefs(arg: "int") -> "str": ...


@pytest.mark.parametrize(
    "obj, type_, expected",
    [
        (3, int, True),
        (True, int, True),
        (3, float, True),
        (True, float, True),
        (b"", float, False),
        (1.5, int, False),
        ("hi", str, True),
        ("hi", t.AnyStr, True),
        ("hi", T, True),
        (b"", str, False),
        ([], tuple, False),
        ([], list, True),
        ([], t.List[int], True),
        ([1], t.List[int], True),
        ([True], t.List[float], True),
        ([1], t.List[str], False),
        (1, t.Union[int, str], True),
        ("hi", t.Union[int, str], True),
        (b"", t.Union[int, str], False),
        (None, t.Optional[int], True),
        (1, t.Optional[int], True),
        (b"", t.Optional[int], False),
        (1, t.Annotated[int, "hi"], True),
        ((), tuple, True),
        ((), t.Tuple, True),
        ((), t.Tuple[int], False),
        ((1, "str"), t.Tuple[int, str], True),
        ((), t.Tuple[int, ...], True),
        ((1, 2), t.Tuple[int, ...], True),
        ((1, b""), t.Tuple[int, ...], False),
        (dict, t.Callable[[], t.Any], True),
        # (list, Callable[[str], list], True),
        # (list, Callable[[str], List[str]], True),
        (AwaitableObject(), t.Awaitable, True),
        (AwaitableObject(), t.Awaitable[t.Any], True),
        (AwaitableObject(), t.Awaitable[object], True),
        # (AwaitableObject(), Awaitable[int], False),
        (func_with_forwardrefs, t.Callable[[int], str], True),
        (func_with_forwardrefs, t.Callable[[float], str], False),
        (func_with_forwardrefs, t.Callable[[int], bytes], False),
    ],
)
def test_is_instance(obj, type_, expected):
    assert is_instance(obj, type_) == expected


# @pytest.mark.parametrize(
#     "obj, type_, expected",
#     [
#         (3, "ThisIsAnInvalidForwardRef", False),
#         # (3, "datetime", False),  # This is interesting because `datetime` is a module
#     ],
# )
# def test_is_instance_with_forwardref_type(obj, type_, expected):
#     assert is_instance(obj, type_, treat_name_errors_as_imports=True) == expected


@pytest.mark.parametrize(
    "subtype, supertype, expected",
    [
        (dict, t.Any, True),
        (t.Any, dict, True),
        (dict, t.Callable, False),
        (tuple, t.Iterable, True),
        # (List[bool], Sequence[int], True),
        (tuple, t.Union[list, tuple], True),
        (tuple, t.Union[list, t.Iterable], True),
        (t.Iterable, t.Union[list, str], False),
        (tuple, t.Optional[tuple], True),
        (tuple, t.Optional[list], False),
    ],
)
def test_is_subtype(subtype, supertype, expected):
    assert is_subtype(subtype, supertype) == expected


if sys.version_info >= (3, 10):

    @pytest.mark.parametrize(
        "subtype, supertype, expected",
        [
            (tuple, list | tuple, True),
            (tuple, list | t.Iterable, True),
            (t.Iterable, list | str, False),
            (tuple, tuple | None, True),
            (tuple, list | None, False),
        ],
    )
    def test_is_subtype_py30(subtype, supertype, expected):
        assert is_subtype(subtype, supertype) == expected

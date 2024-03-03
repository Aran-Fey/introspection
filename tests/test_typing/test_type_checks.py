import pytest

import sys
from typing import *

from introspection.typing import is_instance, is_subtype


T = TypeVar("T")


class AwaitableObject:
    def __await__(self) -> Iterator[None]: ...


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
        ("hi", AnyStr, True),
        ("hi", T, True),
        (b"", str, False),
        ([], tuple, False),
        ([], list, True),
        ([], List[int], True),
        ([1], List[int], True),
        ([True], List[float], True),
        ([1], List[str], False),
        (1, Union[int, str], True),
        ("hi", Union[int, str], True),
        (b"", Union[int, str], False),
        (None, Optional[int], True),
        (1, Optional[int], True),
        (b"", Optional[int], False),
        ((), tuple, True),
        ((), Tuple, True),
        ((), Tuple[int], False),
        ((1, "str"), Tuple[int, str], True),
        ((), Tuple[int, ...], True),
        ((1, 2), Tuple[int, ...], True),
        ((1, b""), Tuple[int, ...], False),
        (dict, Callable[[], Any], True),
        # (list, Callable[[str], list], True),
        # (list, Callable[[str], List[str]], True),
        (AwaitableObject(), Awaitable, True),
        (AwaitableObject(), Awaitable[Any], True),
        (AwaitableObject(), Awaitable[object], True),
        # (AwaitableObject(), Awaitable[int], False),
        (func_with_forwardrefs, Callable[[int], str], True),
        (func_with_forwardrefs, Callable[[float], str], False),
        (func_with_forwardrefs, Callable[[int], bytes], False),
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
        (dict, Any, True),
        (Any, dict, True),
        (dict, Callable, False),
        (tuple, Iterable, True),
        # (List[bool], Sequence[int], True),
        (tuple, Union[list, tuple], True),
        (tuple, Union[list, Iterable], True),
        (Iterable, Union[list, str], False),
        (tuple, Optional[tuple], True),
        (tuple, Optional[list], False),
    ],
)
def test_is_subtype(subtype, supertype, expected):
    assert is_subtype(subtype, supertype) == expected


if sys.version_info >= (3, 10):

    @pytest.mark.parametrize(
        "subtype, supertype, expected",
        [
            (tuple, list | tuple, True),
            (tuple, list | Iterable, True),
            (Iterable, list | str, False),
            (tuple, tuple | None, True),
            (tuple, list | None, False),
        ],
    )
    def test_is_subtype_py30(subtype, supertype, expected):
        assert is_subtype(subtype, supertype) == expected

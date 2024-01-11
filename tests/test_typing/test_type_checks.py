import pytest

from typing import *

from introspection.typing import is_instance, is_subtype


T = TypeVar("T")


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
        (dict, Callable[[], Any], True),
        (list, Callable[[str], list], True),
        # (list, Callable[[str], List[str]], True),
    ],
)
def test_is_instance(obj, type_, expected):
    assert is_instance(obj, type_) == expected


@pytest.mark.parametrize(
    "subtype, supertype, expected",
    [
        (dict, Any, True),
        (Any, dict, True),
        (dict, Callable, True),
        (tuple, Iterable, True),
        # (List[bool], Sequence[int], True),
    ],
)
def test_is_subtype(subtype, supertype, expected):
    assert is_subtype(subtype, supertype) == expected

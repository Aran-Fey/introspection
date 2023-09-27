
import pytest

from typing import *

from introspection.typing import is_instance, is_subtype


@pytest.mark.parametrize('obj, type_, expected', [
    (dict, Callable[[], Any], True),
])
def test_is_instance(obj, type_, expected):
    assert is_instance(obj, type_) == expected


@pytest.mark.parametrize('subtype, supertype, expected', [
    (dict, Any, True),
    (Any, dict, True),
    (dict, Callable, True),
    (tuple, Iterable, True),
    # (List[bool], Sequence[int], True),
])
def test_is_subtype(subtype, supertype, expected):
    assert is_subtype(subtype, supertype) == expected

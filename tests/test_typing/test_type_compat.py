
import pytest

import collections.abc
import typing

from introspection.typing.type_compat import *


@pytest.mark.parametrize('type_, expected', [
    (typing.List, list),
    (typing.Set, set),
    (typing.Callable, collections.abc.Callable),
    (typing.Any, typing.Any),
    (typing.SupportsFloat, typing.SupportsFloat),
])
def test_to_python(type_, expected):
    assert to_python(type_) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('type_, expected', [
        (typing.Literal, typing.Literal),
    ])
    def test_literal_to_python(type_, expected):
        assert to_python(type_) == expected


@pytest.mark.parametrize('type_, expected', [
    (list, typing.List),
    (set, typing.Set),
    (collections.abc.Callable, typing.Callable),
    (object, object),
    (typing.Any, typing.Any),
    (typing.Callable, typing.Callable),
])
def test_to_typing(type_, expected):
    assert to_typing(type_) == expected

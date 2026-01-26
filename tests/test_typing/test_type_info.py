import typing as t
import types

from introspection.typing import TypeInfo


def test_union():
    info = TypeInfo(int | str)
    assert info.type in (t.Union, types.UnionType)
    assert info.arguments == (int, str)

from __future__ import annotations

import typing as t

import introspection.typing


class GenericFoo[T: int]:
    foo: T


def test_resolve_new_typevar_syntax():
    annotations = introspection.typing.get_instance_attribute_annotations(GenericFoo)

    assert isinstance(annotations["foo"].type, t.TypeVar)
    assert annotations["foo"].type.__bound__ is int

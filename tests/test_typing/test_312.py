from __future__ import annotations

import typing as t

import pytest

import introspection.typing


class GenericFoo[T: int]:
    foo: T


type MyInt = int
type MyList[T] = t.List[T]


def test_resolve_new_typevar_syntax():
    annotations = introspection.typing.get_instance_attribute_annotations(GenericFoo)

    assert isinstance(annotations["foo"].type, t.TypeVar)
    assert annotations["foo"].type.__bound__ is int


@pytest.mark.parametrize(
    "type_, base_cls",
    [
        (MyList[int], MyList),
    ],
)
def test_get_generic_base_class(type_, base_cls):
    assert introspection.typing.get_generic_base_class(type_) == base_cls


@pytest.mark.parametrize(
    "type_, python_type",
    [
        (MyInt, int),
        (MyList, list),
    ],
)
def test_to_python(type_, python_type):
    assert introspection.typing.to_python(type_) == python_type


@pytest.mark.parametrize(
    "value, type_, expected",
    [
        (213, MyInt, True),
        (["foo"], MyList[str], True),
        (["foo"], MyList[float], False),
    ],
)
def test_is_instance_with_type_syntax(value: object, type_, expected: bool):
    assert introspection.typing.is_instance(value, type_) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (MyInt, False),
        (MyList, True),
    ],
)
def test_is_generic(type_, expected: bool):
    assert introspection.typing.is_generic(type_) == expected

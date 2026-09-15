import pytest

import typing

from introspection.typing import (
    is_type,
    is_typing_type,
    is_generic,
    is_newtype,
    get_type_name,
    get_type_parameters,
    TypeInfo,
    is_instance,
    is_subtype,
)
from introspection.typing.misc import annotation_to_string
from introspection.typing.type_compat import to_python, to_typing
from introspection import errors


UserId = typing.NewType("UserId", int)
Email = typing.NewType("Email", str)
NestedNewType = typing.NewType("NestedNewType", UserId)


# --- is_newtype ---


@pytest.mark.parametrize(
    "type_, expected",
    [
        (UserId, True),
        (Email, True),
        (NestedNewType, True),
        (int, False),
        (str, False),
        (typing.List[int], False),
        (typing.Optional[int], False),
        (typing.Union[int, str], False),
    ],
)
def test_is_newtype(type_, expected):
    assert is_newtype(type_) == expected


def test_is_newtype_error():
    with pytest.raises(errors.NotAType):
        is_newtype(3)


def test_is_newtype_non_raising():
    assert not is_newtype("foo", raising=False)
    assert not is_newtype(3, raising=False)
    assert is_newtype(UserId, raising=False)


# --- is_type with NewType ---


def test_is_type_newtype():
    assert is_type(UserId) is True


# --- is_typing_type with NewType ---


def test_is_typing_type_newtype():
    assert is_typing_type(UserId) is True


def test_is_typing_type_newtype_vs_regular():
    assert is_typing_type(UserId) is True
    assert is_typing_type(int) is False


# --- is_generic with NewType ---


def test_is_generic_newtype():
    assert is_generic(UserId) is False


# --- get_type_name with NewType ---


def test_get_type_name_newtype():
    assert get_type_name(UserId) == "UserId"
    assert get_type_name(Email) == "Email"


# --- get_type_parameters with NewType ---


def test_get_type_parameters_newtype():
    with pytest.raises(errors.NotAGeneric):
        get_type_parameters(UserId)


# --- TypeInfo with NewType ---


def test_type_info_newtype():
    info = TypeInfo(UserId)
    assert info.type is UserId
    assert info.is_generic is False
    assert info.parameters is None
    assert info.arguments is None
    assert info.annotations == ()


def test_type_info_newtype_parameterized():
    # NewType is not generic, so parameterizing it doesn't make sense
    # but passing a parameterized type around a NewType should work
    info = TypeInfo(typing.List[UserId])
    assert info.is_generic is True


# --- to_python with NewType ---


def test_to_python_newtype_non_strict():
    assert to_python(UserId, strict=False) is UserId


def test_to_python_newtype_strict():
    with pytest.raises(errors.NoPythonEquivalent):
        to_python(UserId, strict=True)


# --- to_typing with NewType ---


def test_to_typing_newtype():
    assert to_typing(UserId) is UserId


def test_to_typing_newtype_strict():
    assert to_typing(UserId, strict=True) is UserId


# --- is_instance with NewType ---


@pytest.mark.parametrize(
    "obj, type_, expected",
    [
        (42, UserId, True),
        (True, UserId, True),
        ("hi", UserId, False),
        (None, UserId, False),
        ([], UserId, False),
        ("hello", Email, True),
        (42, Email, False),
        (42, NestedNewType, True),
    ],
)
def test_is_instance_newtype(obj, type_, expected):
    assert is_instance(obj, type_) == expected


# --- is_subtype with NewType ---


@pytest.mark.parametrize(
    "subtype, supertype, expected",
    [
        (UserId, int, True),
        (int, UserId, True),
        (UserId, str, False),
        (UserId, UserId, True),
        (Email, str, True),
        (str, Email, True),
        (NestedNewType, int, True),
        (int, NestedNewType, True),
    ],
)
def test_is_subtype_newtype(subtype, supertype, expected):
    assert is_subtype(subtype, supertype) == expected


# --- annotation_to_string with NewType ---


def test_annotation_to_string_newtype():
    result = annotation_to_string(UserId)
    assert "UserId" in result
    # Should include module path for user-defined types
    assert result == f"{UserId.__module__}.UserId"

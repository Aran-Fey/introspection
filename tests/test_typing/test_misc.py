import pytest

import builtins
import io
import sys
import typing
from typing import *

from introspection.typing.misc import *


T = TypeVar("T")

THIS_MODULE = sys.modules[__name__]


@pytest.mark.parametrize(
    "expected",
    [
        "int",
        "List",
        "io.IOBase",
        "List[str]",
        "List['Foo']",
        "Tuple[List[int], bool]",
        "...",
        "Callable[[int], None]",
        "int | str",
        "int | None",
        "int | str | None",
    ],
)
def test_annotation_to_string_simple(expected):
    annotation = eval(expected)

    assert annotation_to_string(annotation) == expected


@pytest.mark.parametrize(
    "expected",
    [
        "Union[int, str]",
        "Union[int, str, None]",
    ],
)
def test_annotation_to_string_old_style_unions(expected):
    annotation = eval(expected)

    assert annotation_to_string(annotation, new_style_unions=False) == expected


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (None, "None"),
        (type(None), "None"),
        (TypeVar("T"), "T"),
        (TypeVar("T", covariant=True), "T"),
        (TypeVar("T", contravariant=True), "T"),
        (TypeVarTuple("T"), "T"),
        (ParamSpec("P"), "P"),
        (ParamSpec("P").args, "P.args"),
        (ParamSpec("P").kwargs, "P.kwargs"),
    ],
)
def test_annotation_to_string(annotation, expected):
    assert annotation_to_string(annotation) == expected


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (TypeVar("T"), "~T"),
        (TypeVar("T", covariant=True), "+T"),
        (TypeVar("T", contravariant=True), "-T"),
        (ParamSpec("P"), "~P"),
        (ParamSpec("P").args, "~P.args"),
        (ParamSpec("P").kwargs, "~P.kwargs"),
    ],
)
def test_annotation_to_string_with_variance_prefixes(annotation, expected):
    assert annotation_to_string(annotation, variance_prefixes=True) == expected


if hasattr(typing, "Literal"):

    @pytest.mark.parametrize(
        "expected",
        [
            "Literal[1, 3, 'foo']",
        ],
    )
    def test_literal_to_string(expected):
        annotation = eval(expected)

        assert annotation_to_string(annotation) == expected


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (int, "int"),
        (List, "typing.List"),
        (List[str], "typing.List[str]"),
        (List[Callable], "typing.List[typing.Callable]"),
    ],
)
def test_annotation_to_string_with_typing(annotation, expected):
    ann = annotation_to_string(annotation, implicit_typing=False)

    assert ann == expected


if hasattr(typing, "Literal"):

    @pytest.mark.parametrize(
        "annotation, expected",
        [
            (Literal[1, 3, "foo"], "typing.Literal[1, 3, 'foo']"),
        ],
    )
    def test_literal_to_string_with_typing(annotation, expected):
        ann = annotation_to_string(annotation, implicit_typing=False)

        assert ann == expected


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (int, int),
        (List, List),
        (List["str"], List[str]),
        (Tuple[Dict["str", "int"]], Tuple[Dict[str, int]]),
        (Tuple["Dict[str, int]"], Tuple[Dict[str, int]]),
        (Callable[["int"], str], Callable[[int], str]),
        ("ellipsis", type(...)),
        ("int if False else float", float),
        ('List["int"]', List[int]),
    ],
)
def test_resolve_forward_refs(annotation, expected):
    assert resolve_forward_refs(annotation) == expected


if hasattr(typing, "Literal"):

    @pytest.mark.parametrize(
        "annotation, expected",
        [
            (Literal["int", "Tuple"], Literal["int", "Tuple"]),
            # (Literal[ForwardRef('int'), 'Tuple'], Literal[int, 'Tuple']),
        ],
    )
    def test_resolve_forward_refs_literal(annotation, expected):
        assert resolve_forward_refs(annotation) == expected


memoryview = bytearray


@pytest.mark.parametrize(
    "annotation, module, expected",
    [
        ("memoryview", THIS_MODULE, bytearray),
        ("memoryview", None, builtins.memoryview),
    ],
)
def test_resolve_forward_refs_in_module(annotation, module, expected):
    ann = resolve_forward_refs(annotation, module=module)
    assert ann == expected


@pytest.mark.parametrize(
    "annotation, module, expected",
    [
        ("io.IOBase", THIS_MODULE, io.IOBase),
    ],
)
def test_resolve_forward_refs_no_eval(annotation, module, expected):
    ann = resolve_forward_refs(annotation, module=module, eval_=False)
    assert ann == expected


@pytest.mark.parametrize(
    "annotation, kwargs",
    [
        ("ThisClassDoesntExist", {"eval_": False}),
        ("ThisClassDoesntExist", {"module": "sys"}),
        ("this is a syntax error", {}),
    ],
)
def test_resolve_forward_refs_error(annotation, kwargs):
    with pytest.raises(ValueError):
        resolve_forward_refs(annotation, **kwargs)


@pytest.mark.parametrize(
    "annotation, kwargs, expected",
    [
        ("ThisClassDoesntExist", {"eval_": False}, "ThisClassDoesntExist"),
        ("this is a syntax error", {}, "this is a syntax error"),
        ('List["Foo"]', {}, List["Foo"]),
    ],
)
def test_resolve_forward_refs_non_strict(annotation, kwargs, expected):
    ann = resolve_forward_refs(annotation, strict=False, **kwargs)
    assert ann == expected


def no_args():
    pass


def nil__nil(x):
    pass


def args_nil(*args):
    pass


def str_args__float(foo: str, *args) -> float:
    return 3


def t_args__t(foo: T, *args) -> T:
    return foo


@pytest.mark.parametrize(
    "callable_, expected",
    [
        (len, Callable[[Sized], int]),
        (
            range,
            Union[
                Callable[[int, int, int], range],
                Callable[[int, int], range],
                Callable[[int], range],
            ],
        ),
        (nil__nil, Callable[[Any], Any]),
        (no_args, Callable[[], Any]),
        # (args_nil, Callable),
        # (str_args__float, Callable[..., float]),
        # (t_args__t, Union[
        #     Callable[[T], T],
        #     Callable[..., T],
        # ]),
    ],
)
def test_annotation_for_callable(callable_, expected):
    ann = annotation_for_callable(callable_)
    assert ann == expected

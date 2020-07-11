
import pytest

import builtins
import io
import sys
import typing
from typing import *

from introspection.typing.misc import *


THIS_MODULE = sys.modules[__name__]


@pytest.mark.parametrize('expected', [
    'int',
    'List',
    'io.IOBase',
    'List[str]',
    "List['Foo']",
    'Tuple[List[int], bool]',
    '...',
    'Callable[[int], None]',
])
def test_annotation_to_string_simple(expected):
    annotation = eval(expected)

    assert annotation_to_string(annotation) == expected


@pytest.mark.parametrize('annotation, expected', [
    (None, 'None'),
    (type(None), 'None'),
])
def test_annotation_to_string(annotation, expected):
    assert annotation_to_string(annotation) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('expected', [
        "Literal[1, 3, 'foo']",
    ])
    def test_literal_to_string(expected):
        annotation = eval(expected)

        assert annotation_to_string(annotation) == expected


@pytest.mark.parametrize('var, expected', [
    (TypeVar('T'), '~T'),
    (TypeVar('T_co', covariant=True), '+T_co'),
    (TypeVar('T_contra', contravariant=True), '-T_contra'),
])
def test_annotation_to_string_typevars(var, expected):
    assert annotation_to_string(var) == expected


@pytest.mark.parametrize('annotation, expected', [
    (int, 'int'),
    (List, 'typing.List'),
    (List[str], 'typing.List[str]'),
    (List[Callable], 'typing.List[typing.Callable]'),
])
def test_annotation_to_string_with_typing(annotation, expected):
    ann = annotation_to_string(annotation, implicit_typing=False)

    assert ann == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('annotation, expected', [
        (Literal[1, 3, 'foo'], "typing.Literal[1, 3, 'foo']"),
    ])
    def test_literal_to_string_with_typing(annotation, expected):
        ann = annotation_to_string(annotation, implicit_typing=False)

        assert ann == expected


@pytest.mark.parametrize('annotation, expected', [
    (int, int),
    (List, List),
    (List['str'], List[str]),
    (Tuple[Dict['str', 'int']], Tuple[Dict[str, int]]),
    (Tuple['Dict[str, int]'], Tuple[Dict[str, int]]),
    (Callable[['int'], str], Callable[[int], str]),
    ('ellipsis', type(...)),
    ('int if False else float', float),
    ('List["int"]', List[int]),
])
def test_resolve_forward_refs(annotation, expected):
    assert resolve_forward_refs(annotation) == expected


if hasattr(typing, 'Literal'):
    @pytest.mark.parametrize('annotation, expected', [
        (Literal['int', 'Tuple'], Literal['int', 'Tuple']),
        # (Literal[ForwardRef('int'), 'Tuple'], Literal[int, 'Tuple']),
    ])
    def test_resolve_forward_refs_literal(annotation, expected):
        assert resolve_forward_refs(annotation) == expected


memoryview = bytearray


@pytest.mark.parametrize('annotation, module, expected', [
    ('memoryview', THIS_MODULE, bytearray),
    ('memoryview', None, builtins.memoryview),
])
def test_resolve_forward_refs_in_module(annotation, module, expected):
    ann = resolve_forward_refs(annotation, module=module)
    assert ann == expected


@pytest.mark.parametrize('annotation, module, expected', [
    ('io.IOBase', THIS_MODULE, io.IOBase),
])
def test_resolve_forward_refs_no_eval(annotation, module, expected):
    ann = resolve_forward_refs(annotation, module=module, eval_=False)
    assert ann == expected


@pytest.mark.parametrize('annotation, kwargs', [
    ('ThisClassDoesntExist', {'eval_': False}),
    ('ThisClassDoesntExist', {'module': 'sys'}),
    ('this is a syntax error', {}),
])
def test_resolve_forward_refs_error(annotation, kwargs):
    with pytest.raises(ValueError):
        resolve_forward_refs(annotation, **kwargs)


@pytest.mark.parametrize('annotation, kwargs, expected', [
    ('ThisClassDoesntExist', {'eval_': False}, 'ThisClassDoesntExist'),
    ('this is a syntax error', {}, 'this is a syntax error'),
    ('List["Foo"]', {}, List['Foo']),
])
def test_resolve_forward_refs_non_strict(annotation, kwargs, expected):
    ann = resolve_forward_refs(annotation, strict=False, **kwargs)
    assert ann == expected

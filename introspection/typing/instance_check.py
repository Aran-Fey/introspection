from __future__ import annotations

import collections.abc
import re
import sys
import types
from typing import *
import typing_extensions

from .introspection import (
    get_type_arguments,
    is_parameterized_generic,
    get_generic_base_class,
)
from ._utils import (
    NOT_INSTANCE_OR_SUBTYPE_CHECKED,
    TypeCheckingConfig,
    resolve_names_in_all_typing_modules,
)
from .subtype_check import _is_subtype
from .type_compat import to_python
from ..errors import CannotResolveForwardref
from ..parameter import Parameter
from ..signature_ import Signature
from .._utils import eval_or_discard
from ..types import Type_, TypeAnnotation, ForwardRefContext

__all__ = ["is_instance"]


T = TypeVar("T")


def is_instance(
    obj: object,
    type_: Union[Type[T], TypeAnnotation],
    *,
    forward_ref_context: ForwardRefContext = None,
    treat_name_errors_as_imports: bool = False,
) -> typing_extensions.TypeGuard[T]:
    """
    Returns whether ``obj`` is an instance of ``type_``. Unlike the builtin
    ``isinstance``, this function supports generics.

    .. warning::
        This function is a work-in-progress and only supports a subset of all
        generic types. If it encounters a type it can't handle, it will throw a
        :exc:`NotImplementedError`.

    .. versionadded:: 1.5
    """
    config = TypeCheckingConfig(forward_ref_context, treat_name_errors_as_imports)
    return _is_instance(config, obj, type_)


def _is_instance(
    config: TypeCheckingConfig,
    obj: object,
    type_: TypeAnnotation,
) -> bool:
    # Make sure we're working with an actual type, not a forward reference
    type_ = config.resolve_at_least_1_level_of_forward_refs(type_)

    # Find out if the type has type parameters
    if not is_parameterized_generic(type_):
        if type_ in TESTS:
            test = TESTS[type_]
            return test(obj)

        if isinstance(type_, TypeVar):
            return _test_typevar(config, obj, type_)

        return _safe_instancecheck(obj, type_)

    # Extract the generic base type and verify if the object is an instance of that
    base_type = get_generic_base_class(type_)
    base_type = to_python(base_type, strict=False)

    if base_type not in NOT_INSTANCE_OR_SUBTYPE_CHECKED:
        if base_type in GENERIC_BASE_TESTS:
            test = GENERIC_BASE_TESTS[base_type]
            result = test(obj)
        else:
            result = _safe_instancecheck(obj, base_type)

        if not result:
            return False

    # Verify the subtypes
    if base_type not in SUBTYPE_TESTS:
        raise NotImplementedError(
            f"`is_instance` currently doesn't support parameterized {base_type!r}"
        )

    subtypes = get_type_arguments(type_)

    test = SUBTYPE_TESTS[base_type]
    return test(config, obj, *subtypes)


def _safe_instancecheck(obj: object, type_: Any) -> bool:
    try:
        return isinstance(obj, type_)
    except TypeError:
        raise NotImplementedError(f"`is_instance` currently doesn't support the type {type_!r}")


def _test_typevar(config: TypeCheckingConfig, obj: object, var: TypeVar) -> bool:
    if var.__bound__ is not None:
        return _is_instance(config, obj, var.__bound__)

    if var.__constraints__:
        return any(_is_instance(config, obj, typ) for typ in var.__constraints__)

    return True


def _test_mapping_subtypes(
    config: TypeCheckingConfig, obj: dict, key_type: Type_, value_type: Type_
) -> bool:
    if key_type in (object, Any) and value_type in (object, Any):
        return True

    for key, value in obj.items():
        if not _is_instance(config, key, key_type):
            return False

        if not _is_instance(config, value, value_type):
            return False

    return True


def _test_tuple_subtypes(config: TypeCheckingConfig, obj: tuple, *subtypes: Type_) -> bool:
    if len(subtypes) == 2 and subtypes[-1] == ...:
        return _test_iterable_subtypes(config, obj, subtypes[0])

    if len(obj) != len(subtypes):
        return False

    return all(_is_instance(config, element, typ) for element, typ in zip(obj, subtypes))


def _test_type_subtypes(config: TypeCheckingConfig, obj: type, type_: Type_) -> bool:
    try:
        return issubclass(obj, type_)  # type: ignore
    except TypeError:
        raise NotImplementedError(f"`is_instance` currently doesn't support the type {type_!r}")


def _test_iterable_subtypes(config: TypeCheckingConfig, obj: Iterable, item_type: Type_) -> bool:
    if item_type in (object, Any):
        return True

    # If the object is an iterator, looping over it would exhaust it. We don't want that.
    if isinstance(obj, collections.abc.Iterator):
        raise NotImplementedError("Can't type check the contents of an iterator")

    return all(_is_instance(config, item, item_type) for item in obj)


def _test_awaitable_subtypes(
    config: TypeCheckingConfig, obj: Awaitable, result_type: Type_
) -> bool:
    if result_type in (object, Any):
        return True

    raise NotImplementedError("Can't type check the result of an Awaitable")


def _test_annotated_subtypes(config: TypeCheckingConfig, obj: Annotated, typ: Type_, *_) -> bool:
    return is_instance(obj, typ)


def _test_callable_subtypes(
    config: TypeCheckingConfig,
    obj: Callable,
    param_types: Union[List[Type_], types.EllipsisType],
    return_type: Type_,
) -> bool:
    signature = Signature.from_callable(obj)
    new_config = TypeCheckingConfig(
        signature.forward_ref_context, config.treat_name_errors_as_imports
    )

    if signature.return_annotation is not Signature.empty:
        if not _is_subtype(new_config, signature.return_annotation, return_type):
            return False

    if param_types is ...:
        # I thought functions with keyword-only arguments wouldn't match, but they do. So this is
        # really just `return True`.
        return True

    parameters = signature.parameter_list
    i = 0
    for param_type in param_types:
        if i >= len(parameters):
            return False

        param = parameters[i]

        if param.kind >= Parameter.KEYWORD_ONLY:
            return False

        if param.annotation is not Parameter.empty:
            # Functions are contravariant in their parameters, so the sub- and supertype are swapped
            # here
            if not _is_subtype(new_config, param_type, param.annotation):
                return False

        if param.kind != Parameter.VAR_POSITIONAL:
            i += 1

    # If any parameters with no default value remain, it's not a match
    return all(param.is_optional for param in parameters[i:])


def _test_literal_subtypes(config: TypeCheckingConfig, obj: object, *options: object) -> bool:
    return obj in options


def _test_optional_subtypes(config: TypeCheckingConfig, obj: object, typ: Type_) -> bool:
    return obj is None or _is_instance(config, obj, typ)


def _test_union_subtypes(config: TypeCheckingConfig, obj: object, *types: Type_) -> bool:
    return any(_is_instance(config, obj, typ) for typ in types)


def _test_regex_pattern_subtypes(
    config: TypeCheckingConfig, pattern: re.Pattern, subtype: Type[AnyStr]
) -> bool:
    return _is_instance(config, pattern.pattern, subtype)


def _test_regex_match_subtypes(
    config: TypeCheckingConfig, match: re.Match, subtype: Type[AnyStr]
) -> bool:
    return _is_instance(config, match.string, subtype)


def _return_true(_) -> bool:
    return True


def _test_literal(value: object) -> bool:
    return isinstance(value, (bool, int, float, str, bytes))


TESTS = {
    Any: _return_true,
    float: lambda value: isinstance(value, (int, float)),
}


GENERIC_BASE_TESTS = resolve_names_in_all_typing_modules(
    {
        "Literal": _test_literal,
        "typing_extensions.Literal": _test_literal,
        "Optional": _return_true,
        "Union": _return_true,
    }
)


SUBTYPE_TESTS: Mapping[object, Callable[..., bool]] = eval_or_discard(
    {
        "dict": _test_mapping_subtypes,
        "frozenset": _test_iterable_subtypes,
        "list": _test_iterable_subtypes,
        "set": _test_iterable_subtypes,
        "tuple": _test_tuple_subtypes,
        "type": _test_type_subtypes,
        "Optional": _test_optional_subtypes,
        "Union": _test_union_subtypes,
        "re.Pattern": _test_regex_pattern_subtypes,
        "re.Match": _test_regex_match_subtypes,
    },
    globals(),
)
SUBTYPE_TESTS.update(  # type: ignore
    resolve_names_in_all_typing_modules(
        {
            "Iterable": _test_iterable_subtypes,
            "Sequence": _test_iterable_subtypes,
            "Mapping": _test_mapping_subtypes,
            "AbstractSet": _test_iterable_subtypes,
            "Set": _test_iterable_subtypes,
            "Awaitable": _test_awaitable_subtypes,
            "Callable": _test_callable_subtypes,
            "Annotated": _test_annotated_subtypes,
            "Literal": _test_literal_subtypes,
        }
    )
)


# Stop the IDE from complaining about unused imports
_ = collections.abc
_ = re

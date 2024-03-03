import types
import typing
from typing_extensions import TypeGuard

from ._utils import (
    NOT_INSTANCE_OR_SUBTYPE_CHECKED,
    TypeCheckingConfig,
    resolve_names_in_all_typing_modules,
)
from .introspection import get_type_arguments, is_parameterized_generic, get_generic_base_class
from .type_compat import to_python
from ..errors import CannotResolveForwardref, NotAParameterizedGeneric
from ..types import Type_, TypeAnnotation, ForwardRefContext

__all__ = ["is_subtype"]


Type_Variable = typing.TypeVar("Type_Variable", bound=Type_)


def is_subtype(
    subtype: TypeAnnotation,
    supertype: Type_Variable,
    *,
    forward_ref_context: ForwardRefContext = None,
    treat_name_errors_as_imports: bool = False,
) -> TypeGuard[typing.Type[Type_Variable]]:
    """
    Returns whether ``subtype`` is a subtype of ``supertype``. Unlike the
    builtin ``issubclass``, this function supports generics.

    .. warning::
        This function is a work-in-progress and only supports a subset of all
        generic types. If it encounters a type it can't handle, it will throw a
        :exc:`NotImplementedError`.

    .. versionadded:: 1.5
    """
    config = TypeCheckingConfig(forward_ref_context, treat_name_errors_as_imports)
    return _is_subtype(config, subtype, supertype)


def _is_subtype(
    config: TypeCheckingConfig,
    subtype: TypeAnnotation,
    supertype: TypeAnnotation,
) -> bool:
    # Make sure we're working with actual types, not forward references
    subtype = config.resolve_at_least_1_level_of_forward_refs(subtype)
    supertype = config.resolve_at_least_1_level_of_forward_refs(supertype)  # type: ignore

    if subtype is typing.Any:
        return True

    if supertype in (typing.Any, object):
        return True

    if not is_parameterized_generic(supertype):
        return _unparameterized_supertype_check(subtype, supertype)

    super_base = get_generic_base_class(supertype)
    if not _unparameterized_supertype_check(subtype, super_base):
        return False

    if super_base in TYPE_ARGS_TESTS:
        test = TYPE_ARGS_TESTS[super_base]
        super_args = get_type_arguments(supertype)
        return test(config, subtype, super_args)

    raise NotImplementedError(f"is_subtype doesn't support parameterized {super_base!r} yet")


def _unparameterized_supertype_check(subtype: Type_, supertype: Type_) -> bool:
    # Check for trivial cases: Everything is a `Union`. Everything is an `Optional`. Etc.
    if supertype in NOT_INSTANCE_OR_SUBTYPE_CHECKED:
        return True

    # Ignore the subtype's type arguments, if it has any. Since the supertype doesn't have any type
    # arguments, which is equivalent to being parameterized with `Any`, the subtype's type arguments
    # don't matter. (This is true even for types with variadic arguments, like `tuple`.)
    try:
        subtype = get_generic_base_class(subtype)
    except NotAParameterizedGeneric:
        pass

    subtype = to_python(subtype, strict=False)
    supertype = to_python(supertype, strict=False)

    try:
        return issubclass(subtype, supertype)  # type: ignore
    except TypeError:
        raise NotImplementedError(f"is_subtype({subtype!r}, {supertype!r}) isn't supported yet")


def _test_union_subtypes(config: TypeCheckingConfig, subtype: Type_, union_types: tuple) -> bool:
    errors: typing.List[Exception] = []

    for union_type in union_types:
        try:
            union_type = config.resolve_at_least_1_level_of_forward_refs(union_type)
        except CannotResolveForwardref as error:
            errors.append(error)
            continue

        if _is_subtype(config, subtype, union_type):
            return True

    if errors:
        raise errors[0]

    return False


def _test_optional_subtypes(
    config: TypeCheckingConfig,
    subtype: Type_,
    optional_type: tuple,  # this is a 1-element tuple
) -> bool:
    if subtype is None or subtype is type(None):
        return True

    return _test_union_subtypes(config, subtype, optional_type)


TYPE_ARGS_TESTS: typing.Mapping[
    Type_, typing.Callable[[TypeCheckingConfig, Type_, typing.Tuple[object, ...]], bool]
] = resolve_names_in_all_typing_modules(
    {
        "Union": _test_union_subtypes,
        "Optional": _test_optional_subtypes,
    }
)

if hasattr(types, "UnionType"):
    TYPE_ARGS_TESTS[types.UnionType] = _test_union_subtypes  # type: ignore

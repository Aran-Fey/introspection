import collections.abc
import typing
from typing_extensions import TypeGuard

from ._utils import TypeCheckingConfig
from .introspection import get_type_arguments, is_parameterized_generic, get_generic_base_class
from .type_compat import to_python
from ..errors import CannotResolveForwardref
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
    try:
        subtype = config.resolve_at_least_1_level_of_forward_refs(subtype)
        supertype = config.resolve_at_least_1_level_of_forward_refs(supertype)  # type: ignore
    except CannotResolveForwardref:
        return False

    if supertype in (typing.Any, object):
        return True

    # Find out if the type has type parameters
    if not is_parameterized_generic(subtype):
        if subtype is typing.Any:
            return True

        # If the subtype has no type arguments, we can just ignore the supertype's arguments - the
        # subtype is effectively parameterized with a bunch of `typing.Any`.
        if is_parameterized_generic(supertype):
            supertype = get_generic_base_class(supertype)

        return _is_subclass(subtype, supertype)

    sub_base = get_generic_base_class(subtype)

    if not is_parameterized_generic(supertype):
        return _is_subclass(sub_base, supertype)

    super_base = get_generic_base_class(supertype)

    try:
        if not _is_subclass(sub_base, super_base):
            return False
    except TypeError:
        return False

    sub_args = get_type_arguments(subtype)
    super_args = get_type_arguments(supertype)

    if super_base in TYPE_ARGS_TESTS:
        test = TYPE_ARGS_TESTS[super_base]
        return test(sub_args, super_args)

    raise NotImplementedError(f"is_subtype doesn't support parameterized {super_base!r} yet")


def _is_subclass(sub_cls: Type_, super_cls: Type_) -> bool:
    sub_cls = to_python(sub_cls, strict=False)
    super_cls = to_python(super_cls, strict=False)

    if super_cls not in SUBCLASS_TESTS:
        try:
            return issubclass(sub_cls, super_cls)  # type: ignore
        except TypeError:
            raise NotImplementedError(f"is_subtype({sub_cls!r}, {super_cls!r}) isn't supported yet")

    test = SUBCLASS_TESTS[super_cls]
    return test(sub_cls)


SUBCLASS_TESTS: typing.Dict[Type_, typing.Callable[[object], bool]] = {
    collections.abc.Callable: callable,
    typing.Callable: callable,
}


def _test_callable_subtypes(sub_args, super_args) -> bool:
    raise NotImplementedError


TYPE_ARGS_TESTS: typing.Mapping[
    Type_, typing.Callable[[typing.Sequence[object], typing.Sequence[object]], bool]
] = {
    collections.abc.Callable: _test_callable_subtypes,
    typing.Callable: _test_callable_subtypes,
}

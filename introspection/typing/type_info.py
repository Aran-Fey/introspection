from __future__ import annotations

import typing
import typing_extensions

from ._utils import resolve_at_least_1_level_of_forward_refs
from .introspection import (
    is_parameterized_generic,
    get_type_arguments,
    get_generic_base_class,
    get_type_parameters,
)
from .type_compat import to_python
from ..errors import NotAGeneric
from ..types import Type_, TypeAnnotation, ForwardRefContext, TypeParameter
from .._utils import cached_property


__all__ = ["TypeInfo"]


class TypeInfo:
    def __init__(
        self,
        type_: TypeAnnotation,
        *,
        forward_ref_context: ForwardRefContext = None,
        treat_name_errors_as_imports: bool = False,
    ):
        resolved_type: Type_ = resolve_at_least_1_level_of_forward_refs(
            type_, forward_ref_context, treat_name_errors_as_imports
        )

        self.annotations = []

        args = None
        while is_parameterized_generic(resolved_type):
            args = get_type_arguments(resolved_type)
            resolved_type = get_generic_base_class(resolved_type)

            if resolved_type is typing_extensions.Annotated:
                self.annotations += args[1:]
                resolved_type = resolve_at_least_1_level_of_forward_refs(
                    args[0],  # type: ignore
                    forward_ref_context,
                    treat_name_errors_as_imports,
                )

        self.type: Type_ = to_python(resolved_type, strict=False)
        self._arguments = args
        self._context = forward_ref_context

    @cached_property
    def parameters(self) -> typing.Optional[typing.Tuple[TypeParameter, ...]]:
        try:
            return get_type_parameters(self.type)
        except NotAGeneric:
            return None

    # @cached_property
    # def arguments(self) -> typing.Optional[typing.Tuple[object, ...]]:
    #     if self._arguments is None:
    #         return None

    #     return tuple(Annotation(arg, context=self._context) for arg in self._arguments)
    @property
    def arguments(self) -> typing.Optional[typing.Tuple[object, ...]]:
        return self._arguments

    @property
    def is_generic(self) -> bool:
        return self.parameters is not None

    @property
    def is_fully_parameterized_generic(self) -> bool:
        return self.parameters == ()

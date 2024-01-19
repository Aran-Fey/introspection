import collections.abc
import dataclasses
import importlib
import sys
import types
import typing
from typing import Iterator

from .misc import resolve_forward_refs, is_forward_ref
from ..errors import CannotResolveForwardref
from ..types import Type_, TypeAnnotation, ForwardRefContext


@dataclasses.dataclass
class TypeCheckingConfig:
    forward_ref_context: ForwardRefContext
    treat_name_errors_as_imports: bool

    def resolve_at_least_1_level_of_forward_refs(self, annotation: TypeAnnotation) -> Type_:
        return resolve_at_least_1_level_of_forward_refs(
            annotation,
            self.forward_ref_context,  # type: ignore[wtf]
            self.treat_name_errors_as_imports,
        )


def resolve_at_least_1_level_of_forward_refs(
    annotation: TypeAnnotation, context: ForwardRefContext, treat_name_errors_as_imports: bool
) -> Type_:
    # Given a forward reference as input, this function resolves the outermost type, but may leave
    # subtypes unevaluated. If the input isn't a forward reference, it is returned as-is.
    if not isinstance(annotation, (str, typing.ForwardRef)):
        return annotation

    # We could set max_depth=1, but that would probably be a waste. There's a good chance that the
    # whole annotation will be resolved anyway, so it's more efficient to do it in one go.
    result = resolve_forward_refs(
        annotation,
        context,
        mode="ast",
        strict=False,
        treat_name_errors_as_imports=treat_name_errors_as_imports,
    )

    if is_forward_ref(result):
        raise CannotResolveForwardref(annotation, context)

    return result  # type: ignore


class ImporterDict(collections.abc.Mapping[str, types.ModuleType]):
    def __getitem__(self, name: str) -> types.ModuleType:
        try:
            return sys.modules[name]
        except KeyError:
            pass

        try:
            return importlib.import_module(name)
        except ImportError:
            raise KeyError(name)

    def __iter__(self) -> Iterator[str]:
        yield from ()

    def __len__(self) -> int:
        return 0


import typing
import typing_extensions

from .introspection import is_forwardref, is_parameterized_generic, get_type_arguments, get_generic_base_class, get_type_parameters
from .misc import resolve_forward_refs, ForwardRefContext
from .type_compat import to_python
from ..errors import NotAGeneric
from ..types import TypeAnnotation
from .._utils import cached_property


__all__ = ['Annotation']


class Annotation:
    def __init__(self, type_: TypeAnnotation, *, context: ForwardRefContext = None):
        if is_forwardref(type_):
            type_ = resolve_forward_refs(type_, context, strict=False)
        else:
            assert context is None, "Context must be None if the input type is not a forward reference"

        self.annotations = []

        args = None
        while is_parameterized_generic(type_):
            args = get_type_arguments(type_)
            type_ = get_generic_base_class(type_)

            if type_ is typing_extensions.Annotated:
                type_ = args[0]
                self.annotations += args[1:]
        
        self.type = to_python(type_, strict=False)
        self._arguments = args
    
    @cached_property
    def parameters(self) -> typing.Optional[typing.Tuple[typing.TypeVar, ...]]:
        try:
            return get_type_parameters(self.type)
        except NotAGeneric:
            return None
    
    @cached_property
    def arguments(self) -> typing.Optional[typing.Tuple[object, ...]]:
        if self._arguments is None:
            return None
        
        return tuple(Annotation(arg) for arg in self._arguments)
    
    @property
    def is_generic(self) -> bool:
        return self.parameters is not None
    
    @property
    def is_fully_parameterized_generic(self) -> bool:
        return self.parameters == ()
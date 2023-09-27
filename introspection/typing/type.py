
import typing

from .introspection import *
from .type_compat import *
from ..types import Type_


__all__ = ['Type']


class Type:
    is_parameterized_generic: bool
    class_: typing.Optional[type]
    generic_base_class: typing.Optional[Type_]
    type_arguments: typing.Optional[typing.Tuple[object, ...]]
    type_parameters: typing.Optional[typing.Tuple[typing.TypeVar, ...]]

    def __init__(self, annotation: Type_) -> None:
        self.is_parameterized_generic = is_parameterized_generic(annotation)

        if self.is_parameterized_generic:
            self.generic_base_class = get_generic_base_class(annotation)
            self.type_arguments = get_type_arguments(annotation)
            self.type_parameters = get_type_parameters(annotation)

            try:
                self.class_ = to_python(self.generic_base_class, strict=True)
            except TypeError:
                self.class_ = None
        else:
            self.generic_base_class = None
            self.type_arguments = None
            self.type_parameters = None

            try:
                self.class_ = to_python(annotation, strict=True)
            except TypeError:
                self.class_ = None

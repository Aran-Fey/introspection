import types
import dataclasses
from typing import *
import typing_extensions

from .types import *
from . import call_frame


__all__ = [
    "Error",
    "FunctionCallError",
    "ArgumentError",
    "ArgumentRequired",
    "InvalidArgumentType",
    "InvalidOption",
    "NotAType",
    "NotAGeneric",
    "NotAParameterizedGeneric",
    "ForwardRefsDontHaveNames",
    "GenericMustNotBeParameterized",
    "ConflictingArguments",
    "SubTypeRequired",
    "NameNotAccessibleFromFrame",
    "DundermethodNotFound",
    "ObjectHasNoDict",
    "CannotUnwrapBoundMethod",
    "InvalidIdentifier",
    "NoSignatureFound",
    "MethodNotFound",
    "TypeVarNotSet",
    "NoConcreteTypeForTypeVar",
    "CannotResolveForwardref",
    "NoTypingEquivalent",
    "NoPythonEquivalent",
    "NoGenericPythonEquivalent",
]


T_co = TypeVar("T_co", covariant=True)
V_co = TypeVar("V_co", covariant=True)
M_co = TypeVar("M_co", covariant=True, bound=Union[type, Iterable[type]])


@typing_extensions.dataclass_transform()
class Error(Exception):
    def __init_subclass__(cls):
        dataclasses.dataclass(eq=False, frozen=True)(cls)


class FunctionCallError(Error):
    pass
    # function: Callable = dataclasses.field(init=False)

    # def __post_init__(self):
    #     self.function = 'TODO'


class ArgumentError(FunctionCallError):
    parameter: str


class InvalidArgumentError(Generic[V_co], ArgumentError):
    value: V_co

    def __str__(self) -> str:
        return f"Invalid value for parameter {self.parameter!r}: {self.value!r}"


class ArgumentRequired(ArgumentError):
    reason: str

    def __str__(self) -> str:
        return f"Because {self.reason}, the {self.parameter!r} argument is required"


class InvalidArgumentType(InvalidArgumentError[V_co], Generic[V_co, T_co], TypeError):
    expected_type: Type[T_co]

    def __str__(self) -> str:
        return super().__str__() + f". A value of type {self.expected_type!r} is required."


class InvalidOption(InvalidArgumentError[V_co], Generic[V_co, T_co], ValueError):
    options: Set[T_co]

    def __str__(self) -> str:
        return super().__str__() + f". Valid options are: {self.options}"


class NotAType(InvalidArgumentError[V_co], TypeError):
    def __str__(self) -> str:
        return super().__str__() + f". A class or type is required."


class NotAGeneric(InvalidArgumentError[V_co], ValueError):
    def __str__(self) -> str:
        return super().__str__() + f". A generic type is required."


class NotAParameterizedGeneric(InvalidArgumentError[V_co], ValueError):
    def __str__(self) -> str:
        return super().__str__() + f". A parameterized generic is required."


class ForwardRefsDontHaveNames(InvalidArgumentError[V_co], TypeError):
    def __str__(self) -> str:
        return super().__str__() + f". ForwardRefs don't have names."


class GenericMustNotBeParameterized(InvalidArgumentError[V_co], ValueError):
    def __str__(self) -> str:
        return super().__str__() + f". Only unparameterized generics are allowed."


class ObjectHasNoDict(InvalidArgumentError[V_co], TypeError):
    def __str__(self) -> str:
        return super().__str__() + f". It doesn't have a __dict__."


class ConflictingArguments(FunctionCallError, TypeError):
    parameter1: str
    parameter2: str

    def __str__(self) -> str:
        return f"You cannot pass {self.parameter1!r} and {self.parameter2!r} at the same time"


class SubTypeRequired(FunctionCallError, ValueError):
    type: Type_
    base_type: Type_

    def __str__(self) -> str:
        return f"{self.type!r} isn't a subtype of {self.base_type!r}"


class NameNotAccessibleFromFrame(Error, NameError):
    name: str
    frame: "call_frame.CallFrame"

    def __str__(self) -> str:
        return f"Name {self.name!r} is not accessible from frame {self.frame!r}"


class DundermethodNotFound(Error, AttributeError):
    method_name: str
    cls: type

    def __str__(self) -> str:
        return f"Class {self.cls!r} doesn't implement {self.method_name}"


class CannotUnwrapBoundMethod(Error, TypeError):
    method: types.MethodType

    def __str__(self) -> str:
        return f"Cannot unwrap a bound method"


class InvalidIdentifier(Error, NameError):
    identifier: str

    def __str__(self) -> str:
        return f"Failed to resolve identifier {self.identifier!r}"


class NoSignatureFound(Error, ValueError):
    callable: Callable[..., object]

    def __str__(self) -> str:
        return f"Can't determine signature of {self.callable!r}"


class MethodNotFound(Error, AttributeError, Generic[M_co]):
    method_name: str
    class_or_mro: M_co

    def __str__(self) -> str:
        return f"No method named {self.method_name!r} found in {self.class_or_mro}"


class TypeVarNotSet(Error):
    type_var: TypeVar
    base_type: type
    type: type

    def __str__(self) -> str:
        return f"TypeVar {self.type_var} of {self.base_type!r} is not set in {self.type!r}"


class NoConcreteTypeForTypeVar(Error):
    type_var: TypeVar
    base_type: type
    type: type
    final_var: TypeVar

    def __str__(self) -> str:
        return (
            f"TypeVar {self.type_var} of {self.base_type!r} doesn't have a concrete value in"
            f" {self.type!r}; it is set to {self.final_var!r}"
        )


class CannotResolveForwardref(Error, ValueError):
    forward_ref: ForwardReference
    context: ForwardRefContext

    def __str__(self) -> str:
        return f"Cannot resolve forward reference {self.forward_ref!r} in context {self.context!r}"


class NoTypingEquivalent(Error, ValueError):
    type: type

    def __str__(self) -> str:
        return f"{self.type!r} has no typing equivalent"


class NoPythonEquivalent(Error, ValueError):
    type: Type_

    def __str__(self) -> str:
        return f"{self.type!r} has no plain python equivalent"


class NoGenericPythonEquivalent(Error, ValueError):
    type: Type_

    def __str__(self) -> str:
        return f"{self.type!r} has no (generic) plain python equivalent"

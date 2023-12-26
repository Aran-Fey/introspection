import types
import dataclasses
from typing import *  # type: ignore

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


class Error(Exception):
    _STR: ClassVar[str]

    def __init_subclass__(cls):
        dataclasses.dataclass(eq=False, frozen=True)(cls)

    def __str__(self):
        f_string_template = f"f{self._STR!r}"
        return eval(f_string_template, vars(self))


class FunctionCallError(Error):
    pass
    # function: Callable = dataclasses.field(init=False)

    # def __post_init__(self):
    #     self.function = 'TODO'


class ArgumentError(Generic[V_co], FunctionCallError):
    parameter: str
    value: V_co

    def __init_subclass__(cls):
        cls._STR = "Invalid value for parameter {parameter!r}: {value!r}. " + cls._STR

        super().__init_subclass__()


class ArgumentRequired(ArgumentError[V_co]):
    parameter: str
    reason: str

    _STR = "Because {reason}, the {parameter!r} argument is required"


class InvalidArgumentType(ArgumentError[V_co], Generic[V_co, T_co], TypeError):
    expected_type: Type[T_co]

    _STR = "A value of type {expected_type!r} is required."


class InvalidOption(ArgumentError[V_co], Generic[V_co, T_co], ValueError):
    options: Set[T_co]

    _STR = "Valid options are: {options}"


class NotAType(ArgumentError[V_co], TypeError):
    _STR = "A class or type is required."


class NotAGeneric(ArgumentError[V_co], ValueError):
    _STR = "A generic type is required."


class NotAParameterizedGeneric(ArgumentError[V_co], ValueError):
    _STR = "A parameterized generic is required."


class ForwardRefsDontHaveNames(ArgumentError[V_co], TypeError):
    _STR = "ForwardRefs don't have names."


class GenericMustNotBeParameterized(ArgumentError[V_co], ValueError):
    _STR = "Only unparameterized generics are allowed."


class ConflictingArguments(FunctionCallError, TypeError):
    parameter1: str
    parameter2: str

    _STR = "You cannot pass {parameter1!r} and {parameter2!r} at the same time"


class SubTypeRequired(FunctionCallError, ValueError):
    type: Type_
    base_type: Type_

    _STR = "{type!r} isn't a subtype of {base_type!r}"


class NameNotAccessibleFromFrame(Error, NameError):
    name: str
    frame: "call_frame.CallFrame"

    _STR = "Name {name!r} is not accessible from frame {frame!r}"


class DundermethodNotFound(Error, AttributeError):
    method_name: str
    cls: type

    _STR = "Class {cls!r} doesn't implement {method_name}"


class ObjectHasNoDict(ArgumentError[V_co], TypeError):
    _STR = "It doesn't have a __dict__."


class CannotUnwrapBoundMethod(Error, TypeError):
    method: types.MethodType

    _STR = "Cannot unwrap a bound method"


class InvalidIdentifier(Error, NameError):
    identifier: str

    _STR = "Failed to resolve identifier {identifier!r}"


class NoSignatureFound(Error, ValueError):
    callable: Callable[..., object]

    _STR = "Can't determine signature of {callable!r}"


class MethodNotFound(Error, AttributeError, Generic[M_co]):
    method_name: str
    class_or_mro: M_co

    _STR = "No method named {method_name!r} found in {class_or_mro}"


class TypeVarNotSet(Error):
    _STR = "TypeVar {type_var} of {base_type!r} is not set in {type!r}"


class NoConcreteTypeForTypeVar(Error):
    final_var: TypeVar

    _STR = "TypeVar {type_var} of {base_type!r} doesn't have a concrete value in {type!r}; it is set to {final_var!r}"


class CannotResolveForwardref(Error, ValueError):
    name: str
    context: ForwardRefContext

    _STR = "Cannot resolve name {name!r} with context {context!r}"


class NoTypingEquivalent(Error, ValueError):
    type: type

    _STR = "{type!r} has no typing equivalent"


class NoPythonEquivalent(Error, ValueError):
    type: Type_

    _STR = "{type!r} has no plain python equivalent"


class NoGenericPythonEquivalent(Error, ValueError):
    type: Type_

    _STR = "{type!r} has no (generic) plain python equivalent"

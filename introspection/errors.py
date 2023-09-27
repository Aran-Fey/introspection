import types
import typing
import dataclasses

from .types import *

if typing.TYPE_CHECKING:
    from .call_frame import CallFrame


T_co = typing.TypeVar("T_co", covariant=True)
V_co = typing.TypeVar("V_co", covariant=True)
M_co = typing.TypeVar(
    "M_co", covariant=True, bound=typing.Union[type, typing.Iterable[type]]
)


class Error(Exception):
    def __init_subclass__(cls):
        dataclasses.dataclass(eq=False, frozen=True)(cls)

    def __str__(self):
        f_string_template = f"f{self._STR!r}"
        return eval(f_string_template, vars(self))


class FunctionCallError(Error):
    pass
    # function: typing.Callable = dataclasses.field(init=False)

    # def __post_init__(self):
    #     self.function = 'TODO'


class ArgumentError(typing.Generic[V_co], FunctionCallError):
    parameter: str
    value: V_co

    def __init_subclass__(cls):
        cls._STR = "Invalid value for parameter {parameter!r}: {value!r}. " + cls._STR

        super().__init_subclass__()


class ArgumentRequired(ArgumentError[V_co]):
    parameter: str
    reason: str

    _STR = "Because {reason}, the {parameter!r} argument is required"


class InvalidArgumentType(ArgumentError[V_co], typing.Generic[V_co, T_co], TypeError):
    expected_type: typing.Type[T_co]

    _STR = "A value of type {expected_type!r} is required."


class InvalidOption(ArgumentError[V_co], typing.Generic[V_co, T_co], ValueError):
    options: typing.Set[T_co]

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
    frame: "CallFrame"

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
    callable: typing.Callable

    _STR = "Can't determine signature of {callable!r}"


class MethodNotFound(Error, AttributeError, typing.Generic[M_co]):
    method_name: str
    class_or_mro: M_co

    _STR = "No method named {method_name!r} found in {class_or_mro}"


class TypeVarError(Error):
    type_var: typing.TypeVar
    base_type: GenericType
    type: GenericType


class TypeVarNotSet(Error):
    _STR = "TypeVar {type_var} of {base_type!r} is not set in {type!r}"


class NoConcreteTypeForTypeVar(Error):
    final_var: typing.TypeVar

    _STR = "TypeVar {type_var} of {base_type!r} doesn't have a concrete value in {type!r}; it is set to {final_var!r}"


class CannotResolveName(Error, ValueError):
    name: str
    module: typing.Optional[types.ModuleType]

    _STR = "Cannot resolve name {name!r}{' in module {!r}'.format(module.__name__) if module else ''}"


class NoTypingEquivalent(Error, ValueError):
    type: type

    _STR = "{type!r} has no typing equivalent"


class NoPythonEquivalent(Error, ValueError):
    type: Type_

    _STR = "{type!r} has no plain python equivalent"


class NoGenericPythonEquivalent(Error, ValueError):
    type: Type_

    _STR = "{type!r} has no (generic) plain python equivalent"

import types
import typing
import typing_extensions

import sentinel  # type: ignore[reportMissingTypeStubs]


NONE = sentinel.create("NONE")


_GenericAliases = [
    (types, "GenericAlias"),
    (typing, "_GenericAlias"),
]
GenericAliases = tuple(
    getattr(module, name) for module, name in _GenericAliases if hasattr(module, name)
)


T = typing.TypeVar("T")
P = typing_extensions.ParamSpec("P")
Class = typing.TypeVar("Class", bound=type)

Function = types.FunctionType
ParameterizedGeneric: typing_extensions.TypeAlias = "types.GenericAlias"
Type_ = typing.Union[type, typing.TypeVar, ParameterizedGeneric]
TypeAnnotation = typing.Union[Type_, str, typing.ForwardRef, None]


class Slot(typing.Protocol[T]):  # type: ignore[reportInvalidTypeVarUse]
    def __get__(self, instance: T, owner: typing.Optional[typing.Type[T]]) -> object:
        ...

    def __set__(self, instance: T, value: object) -> None:
        ...

    def __delete__(self, instance: T) -> None:
        ...


ForwardRefContext = typing.Union[
    None, type, types.FunctionType, types.ModuleType, str, typing.Mapping[str, object]
]


class ObjectWithQualname(typing.Protocol):
    __name__: str
    __qualname__: str

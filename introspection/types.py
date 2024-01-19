import types
import typing
import typing_extensions

import sentinel


__all__ = [
    "TypeParameter",
    "Type_",
    "ParameterizedGeneric",
    "ForwardReference",
    "TypeAnnotation",
    "ForwardRefContext",
]


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

TypeParameter = typing.Union[typing.TypeVar, typing_extensions.TypeVarTuple]
Function = types.FunctionType
ParameterizedGeneric: typing_extensions.TypeAlias = "types.GenericAlias"
Type_ = typing.Union[type, typing.TypeVar, ParameterizedGeneric, None]
ForwardReference = typing.Union[str, typing.ForwardRef]
TypeAnnotation = typing.Union[Type_, ForwardReference]
ForwardRefContext = typing.Union[
    None, type, types.FunctionType, types.ModuleType, str, typing.Mapping[str, object]
]


# class _MetaGeneric(typing_extensions.Protocol[T]):  # type: ignore
#     def __getitem__(self, subtypes: typing.Union[T, typing.Tuple[T, ...]]) -> ParameterizedGeneric:
#         ...


# class _ClassGeneric(typing_extensions.Protocol[T]):  # type: ignore
#     def __class_getitem__(
#         cls, subtypes: typing.Union[T, typing.Tuple[T, ...]]
#     ) -> ParameterizedGeneric:
#         ...


# GenericType = typing.Union[_MetaGeneric[T], typing.Type[_ClassGeneric[T]]]


class Slot(typing.Protocol[T]):  # type: ignore[variance]
    def __get__(self, instance: T, owner: typing.Optional[typing.Type[T]]) -> object:
        ...

    def __set__(self, instance: T, value: object) -> None:
        ...

    def __delete__(self, instance: T) -> None:
        ...


class ObjectWithQualname(typing.Protocol):
    __name__: str
    __qualname__: str

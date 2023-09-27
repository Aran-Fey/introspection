import types
import typing
import typing_extensions

import sentinel


NONE = sentinel.create("NONE")


GenericAliases = []
for alias in ("types.GenericAlias", "typing._GenericAlias"):
    try:
        GenericAliases.append(eval(alias))
    except AttributeError:
        pass
GenericAliases = tuple(GenericAliases)


T = typing.TypeVar("T")
P = typing_extensions.ParamSpec("P")
Class = typing.TypeVar("Class", bound=type)

Type_ = typing.Union[type, *GenericAliases]
TypeAnnotation = typing.Union[Type_, str, typing.ForwardRef, None]

ParameterizedGeneric = typing.Union[GenericAliases]

Function = types.FunctionType


class GenericType(typing.Protocol):
    def __class_getitem__(cls, item) -> ParameterizedGeneric:
        ...


class Slot(typing.Protocol[T]):
    def __get__(self, instance: T, owner: typing.Optional[typing.Type[T]]) -> object:
        ...

    def __set__(self, instance: T, value: object) -> None:
        ...

    def __delete__(self, instance: T) -> None:
        ...

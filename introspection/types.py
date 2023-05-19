
import types
import typing
import typing_extensions

import sentinel


if hasattr(typing, 'ForwardRef'):
    ForwardRef = typing.ForwardRef
else:
    ForwardRef = typing._ForwardRef


NONE = sentinel.create('NONE')


class GenericType(typing_extensions.Protocol):
    def __class_getitem__(cls, item) -> types.GenericAlias: ...


T = typing.TypeVar('T')
P = typing_extensions.ParamSpec('P')
Class = typing.TypeVar('Class', bound=type)

Type_ = typing.Union[type, types.GenericAlias]
Annotation = typing.Union[Type_, str, ForwardRef]

ParameterizedGeneric = types.GenericAlias

Function = types.FunctionType

class Slot(typing_extensions.Protocol[T]):
    def __get__(self, instance: T, owner: typing.Optional[typing.Type[T]]) -> object: ...
    def __set__(self, instance: T, value: object) -> None: ...
    def __delete__(self, instance: T) -> None: ...

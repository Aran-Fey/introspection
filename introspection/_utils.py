from typing import *
from typing_extensions import Self

S = TypeVar("S")
T = TypeVar("T")


def eval_or_discard(
    mapping: Mapping[str, T],
    namespace: Optional[Dict[str, Any]] = None,
) -> Mapping[object, T]:
    result = {}

    for key, value in mapping.items():
        try:
            key = eval(key, namespace)
        except AttributeError:
            continue

        result[key] = value

    return result


class cached_property(Generic[S, T]):
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    """

    def __init__(self, getter: Callable[[S], T]):
        self._getter = getter

    @overload
    def __get__(self, instance: S, owner: Optional[type] = None) -> T:
        ...

    @overload
    def __get__(self, instance: None, owner: Optional[type] = None) -> Self:
        ...

    def __get__(self, instance: Optional[S], owner: Optional[type] = None) -> Union[T, Self]:
        if instance is None:
            return self

        # Store the value in the instance's __dict__ so that subsequent
        # accesses don't have to go through __get__.
        value = self._getter(instance)
        vars(instance)[self._getter.__name__] = value
        return value


# Sphinx doesn't like it when we use inspect._empty as a default value, so we'll
# use sentinels instead
class _Sentinel:
    def __init__(self, repr_: str):
        self.repr_ = repr_

    def __repr__(self):
        return self.repr_  # pragma: no cover


SIG_EMPTY = _Sentinel("inspect.Signature.empty")
PARAM_EMPTY = _Sentinel("inspect.Parameter.empty")

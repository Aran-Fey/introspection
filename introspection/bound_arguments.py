import collections.abc
import inspect
from typing import *
from typing_extensions import Self, Literal

from . import signature_
from .errors import InvalidOption

__all__ = ["BoundArguments"]


class BoundArguments(inspect.BoundArguments, collections.abc.MutableMapping[str, Any]):
    """
    Subclass of :class:`inspect.BoundArguments` with additional features.

    .. versionadded:: 1.4
    .. versionchanged: 1.5
        Now implements the :class:`~collections.abc.MutableMapping` interface.
    """

    __slots__ = ()

    signature: "signature_.Signature"

    @classmethod
    def from_bound_arguments(cls, bound_args: inspect.BoundArguments) -> Self:
        """
        Creates a new ``BoundArguments`` instance from a
        :class:`inspect.BoundArguments` instance.

        :param bound_args: An :class:`inspect.BoundArguments` instance
        :return: A new ``BoundArguments`` instance
        """
        signature = bound_args.signature

        if not isinstance(signature, signature_.Signature):
            signature = signature_.Signature.from_signature(signature)

        return cls(signature, bound_args.arguments)

    def get_missing_parameter_names(
        self,
        include_optional_parameters: bool = False,
    ) -> Set[str]:
        """
        Returns the set of parameter names that were omitted in the call to
        :meth:`Signature.bind_partial`.

        If ``include_optional_parameters`` is ``True``, parameters with a
        default value are included in the output.

        ``*args`` and ``**kwargs`` are never included in the output.

        Examples::

            >>> signature
            (foo, bar, *args, baz=3)
            >>> bound_args = signature.bind_partial(1)
            >>> bound_args.get_missing_parameter_names()
            {'bar'}
            >>> bound_args.get_missing_parameter_names(True)
            {'bar', 'baz'}

        .. versionadded:: 1.5
        """
        missing = self.signature.parameters.keys() - self.arguments.keys()

        for name, param in self.signature.parameters.items():
            if name not in missing:
                continue

            if param.is_vararg or (not include_optional_parameters and param.is_optional):
                missing.remove(name)

        return missing

    def __getitem__(self, param_name: str) -> Any:
        return self.arguments[param_name]

    def __setitem__(self, param_name: str, value: object) -> None:
        self.arguments[param_name] = value

    def __delitem__(self, param_name: str) -> None:
        del self.arguments[param_name]

    def __iter__(self) -> Iterator[str]:
        return iter(self.arguments)

    def __len__(self) -> int:
        return len(self.arguments)

    def to_varargs(
        self,
        prefer: Literal["args", "kwargs"] = "kwargs",
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Converts the arguments into an ``(args, kwargs)`` tuple.

        Example::

            >>> signature = Signature.from_callable(lambda a, *b, c: 0)
            >>> bound_args = signature.bind(1, c=2)
            >>> bound_args.to_varargs(prefer='args')
            ([1], {'c': 2})
            >>> bound_args.to_varargs(prefer='kwargs')
            ([], {'a': 1, 'c': 2})

        :param prefer: Whether to prefer positional or keyword arguments
        :return: An ``(args, kwargs)`` tuple
        """
        if prefer == "args":
            return list(self.args), self.kwargs
        elif prefer != "kwargs":
            raise InvalidOption("prefer", prefer, {"args", "kwargs"})

        params = list(self.signature.parameters.values())
        args: List[object] = []
        kwargs: Dict[str, object] = {}

        for param in params:
            try:
                value = self.arguments[param.name]
            except KeyError:
                continue

            if param.kind is inspect.Parameter.POSITIONAL_ONLY:
                args.append(value)
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                # If there are so many positional arguments that they have to go
                # into *args, then all previous arguments must also be passed in
                # as positional arguments.
                # Consider the following function:
                #   def func(a, *b):
                # It's possible to call this with a keyword argument:
                #   func(a=1)
                # But if there are at least 2 positional arguments, "a" can no
                # longer be passed in as a keyword argument:
                #   func(1, 2)
                # So we'll convert all the keyword arguments we've generated so
                # far into positional arguments.
                if kwargs:
                    for p in params[: len(kwargs)]:
                        args.append(kwargs.pop(p.name))

                args.extend(value)
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                kwargs.update(value)
            else:
                kwargs[param.name] = value

        return args, kwargs

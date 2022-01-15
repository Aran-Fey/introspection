
import inspect
import typing
from typing import *

__all__ = ['BoundArguments']


class BoundArguments(inspect.BoundArguments):
    """
    Subclass of :class:`inspect.BoundArguments` with additional features.

    .. versionadded: 1.4
    """
    __slots__ = ()

    @classmethod
    def from_bound_arguments(cls, bound_args: inspect.BoundArguments) -> 'BoundArguments':
        """
        Creates a new ``BoundArguments`` instance from a
        :class:`inspect.BoundArguments` instance.

        :param bound_args: An :class:`inspect.BoundArguments` instance
        :return: A new ``BoundArguments`` instance
        """
        from .signature import Signature

        signature = bound_args.signature

        if not isinstance(signature, Signature):
            signature = Signature.from_signature(signature)

        return cls(signature, bound_args.arguments)
    
    def to_varargs(
            self,
            prefer: (typing.Literal['args', 'kwargs'] if hasattr(typing, 'Literal') else str) = 'kwargs',
        ) -> Tuple[list, Dict[str, Any]]:
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
        if prefer == 'args':
            return list(self.args), self.kwargs
        elif prefer != 'kwargs':
            raise ValueError(f"Invalid value for argument 'prefer': {prefer!r}")

        params = list(self.signature.parameters.values())
        args, kwargs = [], {}

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
                    for p in params[:len(kwargs)]:
                        args.append(kwargs.pop(p.name))

                args.extend(value)
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                kwargs.update(value)
            else:
                kwargs[param.name] = value

        return args, kwargs


import inspect

__all__ = ['Parameter']


class Parameter(inspect.Parameter):
    """
    An :class:`inspect.Parameter` subclass that represents a function parameter.

    :ivar name: The parameter's name
    :ivar kind: The parameter's kind. See :attr:`inspect.Parameter.kind` for details.
    :ivar default: The parameter's default value or :attr:`inspect.Parameter.empty`
    :ivar annotation: The parameter's type annotation
    """
    __slots__ = ()

    missing = type('_missing', (), {})

    def __init__(self,
                 name=None,
                 kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                 default=inspect.Parameter.empty,
                 annotation=inspect.Parameter.empty
                 ):
        if kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
            # inspect.Parameter enforces this
            default = Parameter.empty

        super().__init__(name, kind, default=default, annotation=annotation)

    @classmethod
    def from_parameter(cls, parameter: inspect.Parameter) -> 'Parameter':
        """
        Creates a new :class:`Parameter` instance from an :class:`inspect.Parameter` instance.

        :param parameter: An :class:`inspect.Parameter` instance
        :return: A new :class:`Parameter` instance
        """
        return cls(
            parameter.name,
            kind=parameter.kind,
            default=parameter.default,
            annotation=parameter.annotation
        )

    @property
    def is_vararg(self) -> bool:
        """
        Returns a boolean indicating whether this parameter accepts a variable
        number of arguments; i.e. whether the parameter's kind is
        :attr:`inspect.Parameter.VAR_POSITIONAL` or :attr:`inspect.Parameter.VAR_KEYWORD`.
        """

        return self.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}

    @property
    def is_optional(self) -> bool:
        """
        Returns a boolean indicating whether this parameter requires an argument.

        Returns ``False`` if the parameter has a default value or is a vararg.
        """

        return (
            self.default is not self.empty or
            self.is_vararg
        )

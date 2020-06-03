
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

    empty = inspect.Parameter.empty
    missing = type('_missing', (), {})

    def __init__(self, name=None, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, default=empty, annotation=empty):
        if kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
            default = Parameter.empty

        super().__init__(name, kind, default=default, annotation=annotation)

    def copy(self):
        cls = type(self)
        return cls(self.name, self.kind, self.default, self.annotation)

    @property
    def is_optional(self):
        return self.default is not self.empty

    @property
    def default_value(self):
        """
        Synonym for :attr:`Parameter.default`.
        """
        if self.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
            return Parameter.missing

        return self.default

    @default_value.setter
    def default_value(self, value):
        self.default = value

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

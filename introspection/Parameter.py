
import inspect


class Parameter:
    """
    Represents a function parameter.

    Implements the same interface as the :class:`inspect.Parameter` class.

    :ivar name: the parameter's name
    :ivar kind: the parameter's kind. See `inspect.Parameter.kind <https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind>`_ for details.
    :ivar default: the parameter's default value or `Parameter.empty`
    :ivar annotation: the parameter's type annotation
    """

    empty = inspect.Parameter.empty

    POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
    KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
    VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD

    def __init__(self, name=None, kind=POSITIONAL_OR_KEYWORD, default=empty, annotation=empty):
        self.name = name
        self.kind = kind
        self.default = default
        self.annotation = annotation

    @property
    def default_value(self):
        """
        Synonym for `Parameter.default`.
        """
        return self.default

    @default_value.setter
    def default_value(self, value):
        self.default = value

    @classmethod
    def from_parameter(cls, parameter: inspect.Parameter) -> 'Parameter':
        """
        Creates a new `Parameter` instance from an :class:`inspect.Parameter` instance.

        :param parameter: an :class:`inspect.Parameter` instance
        :return: a new `Parameter` instance
        """
        return cls(parameter.name, parameter.kind, default=parameter.default, annotation=parameter.annotation)

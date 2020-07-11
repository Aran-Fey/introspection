
import inspect

from .typing import annotation_to_string

__all__ = ['Parameter']


class Parameter(inspect.Parameter):
    """
    An :class:`inspect.Parameter` subclass that represents a function parameter.

    Instances of this class are immutable.

    This class adds a new special value for the ``default`` attribute: :attr:`Parameter.missing`.
    This value indicates that the parameter is optional, but has no known default value.

    :ivar name: The parameter's name
    :type name: str
    :ivar kind: The parameter's kind. See :attr:`inspect.Parameter.kind` for details.
    :ivar default: The parameter's default value or :attr:`inspect.Parameter.empty`
    :ivar annotation: The parameter's type annotation
    """
    __slots__ = ()

    #: A special class-level marker that can be used to specify
    #: that the parameter is optional, but doesn't have a (known)
    #: default value.
    missing = type('_missing', (), {})

    def __init__(self,
                 name=None,
                 kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                 default=inspect.Parameter.empty,
                 annotation=inspect.Parameter.empty,
                 ):
        """
        :param name: The parameter's name
        :type name: str
        :param kind: The parameter's kind. See :attr:`inspect.Parameter.kind` for details.
        :param default: The parameter's default value or :attr:`inspect.Parameter.empty`
        :param annotation: The parameter's type annotation
        """
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
            annotation=parameter.annotation,
        )

    @property
    def has_annotation(self):
        """
        Returns whether the parameter's :attr:`annotation` is not :attr:`Parameter.empty`.
        """
        return self.annotation is not Parameter.empty

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

    def _to_string_no_brackets(self, implicit_typing):
        text = self.name

        if self.kind is __class__.VAR_POSITIONAL:
            text = '*' + text
        elif self.kind is __class__.VAR_KEYWORD:
            text = '**' + text

        if self.has_annotation:
            ann = annotation_to_string(self.annotation, implicit_typing)
            text += ': {}'.format(ann)

        if self.default not in {__class__.empty, __class__.missing}:
            if self.has_annotation:
                template = '{} = {}'
            else:
                template = '{}={}'

            default = repr(self.default)

            text = template.format(text, default)

        return text

    def to_string(self, implicit_typing=False):
        """
        Returns a string representation of this parameter, similar to
        how parameters are written in function signatures.

        Examples::

            >>> Parameter('foo', Parameter.VAR_POSITIONAL).to_string()
            '*foo'
            >>> Parameter('foo', annotation=int, default=3).to_string()
            'foo: int = 3'
        
        :param implicit_typing: If ``True``, the "typing." prefix will be omitted from types defined in the ``typing`` module
        :return: A string representation of this parameter, like you would see in a function signature
        """
        text = self._to_string_no_brackets(implicit_typing)

        if self.default is __class__.missing:
            text = '[{}]'.format(text)

        return text

    def __repr__(self):
        cls_name = type(self).__name__
        text = self.to_string()

        return '<{} {}>'.format(cls_name, text)

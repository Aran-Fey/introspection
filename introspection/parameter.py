
import inspect

from datatypes import annotation_to_string, annotation_union, annotation_intersection

__all__ = ['Parameter']


class Parameter(inspect.Parameter):
    """
    An :class:`inspect.Parameter` subclass that represents a function parameter.

    This class adds a new special value for the :attr:`default` attribute: :attr:`Parameter.missing`.
    This value indicates that the parameter is optional, but has no known default value.

    :ivar name: The parameter's name
    :type name: str
    :ivar kind: The parameter's kind. See :attr:`inspect.Parameter.kind` for details.
    :ivar default: The parameter's default value or :attr:`inspect.Parameter.empty`
    :ivar annotation: The parameter's type annotation
    :ivar description:
    :type description: Optional[str]
    """
    __slots__ = ('_description',)

    missing = type('_missing', (), {})

    def __init__(self,
                 name=None,
                 kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                 default=inspect.Parameter.empty,
                 annotation=inspect.Parameter.empty,
                 ):
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

    def _to_string_no_brackets(self):
        text = self.name

        if self.kind is __class__.VAR_POSITIONAL:
            text = '*' + text
        elif self.kind is __class__.VAR_KEYWORD:
            text = '**' + text

        if self.has_annotation:
            ann = annotation_to_string(self.annotation)
            text += ': {}'.format(ann)

        if self.default not in {__class__.empty, __class__.missing}:
            if self.has_annotation:
                template = '{} = {}'
            else:
                template = '{}={}'

            default = repr(self.default)

            text = template.format(text, default)

        return text

    def to_string(self):
        text = self._to_string_no_brackets()

        if self.default is __class__.missing:
            text = '[{}]'.format(text)

        return text

    def __repr__(self):
        cls_name = type(self).__name__
        text = self.to_string()

        return '<{} {}>'.format(cls_name, text)

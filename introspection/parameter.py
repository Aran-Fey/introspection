
import inspect
import typing

from . import _parsers
from .misc import annotation_to_string

__all__ = ['Parameter']


class Parameter(inspect.Parameter):
    """
    An :class:`inspect.Parameter` subclass that represents a function parameter.
    
    Instances of this class have an additional attribute: a :attr:`description`.
    The description must be ``None`` or a string. Parameters with no description
    compare equal to regular :class:`inspect.Parameter`s.
    
    This class also adds a new special value for the :attr:`default` attribute: :attr:`Parameter.missing`.
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
                 description=None,
                 ):
        super().__init__(name, kind, default=default, annotation=annotation)
        
        self._description = description

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
            description=parameter.description if isinstance(parameter, __class__) else None,
        )
    
    @classmethod
    def from_string(cls, string, module=None) -> 'Parameter':
        """
        Parses the string representation of a Parameter. This is essentially the opposite of ``repr``.
        
        Examples::
        
            >>> Parameter.from_string('a')
            <Parameter a>
            >>> Parameter.from_string('a: int = 3')
            <Parameter a: int = 3>
        """
        parser = _parsers.parameter_parser(module)
        
        try:
            kwargs = parser(string)
        except SyntaxError:
            raise ValueError('{!r} is not a valid parameter string'.format(string)) from None
        
        return cls(**kwargs)
    
    def replace(self, **attrs):
        kwargs = self._vars()
        kwargs.update(attrs)
        
        return type(self)(**kwargs)
    
    @property
    def description(self) -> typing.Optional[str]:
        return self._description
    
    def __hash__(self):
        # Because parameters with no description compare equal to inspect.Parameters,
        # we must make sure to return the same hash value as well
        if self.description is None:
            return super().__hash__()
        
        return hash((self.name, self.kind, self.default, self.annotation, self.description))
    
    def __eq__(self, other):
        if not isinstance(other, inspect.Parameter):
            return NotImplemented

        if isinstance(other, __class__):
            if self.description != other.description:
                return False
        else:
            # only compare equal to an inspect.Parameter if no description is set
            if self.description is not None:
                return False
            
        return super().__eq__(other)

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
    
    def _vars(self):
        attrs = ('name', 'kind', 'default', 'annotation', 'description')
        return {attr: getattr(self, attr) for attr in attrs}
    
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

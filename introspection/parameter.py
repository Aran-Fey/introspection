import inspect
from typing import *
from typing_extensions import Self

from ._utils import PARAM_EMPTY

__all__ = ["Parameter"]


#: Enum of parameter kinds (POSITIONAL_ONLY, etc.)
ParameterKind = inspect._ParameterKind


class Parameter(inspect.Parameter):
    """
    An :class:`inspect.Parameter` subclass that represents a function parameter.

    Instances of this class are immutable.

    This class adds a new special value for the ``default`` attribute: :attr:`Parameter.missing`.
    """

    __slots__ = ()

    #: A special class-level marker that can be used to specify
    #: that the parameter is optional, but doesn't have a (known)
    #: default value.
    #:
    #: This is commonly used by signatures for builtin functions.
    #: For example, the signature of the :class:`range` function
    #: can be represented as
    #:
    #: ::
    #:
    #:     >>> Signature([
    #:     ...     Parameter('start', Parameter.POSITIONAL_ONLY),
    #:     ...     Parameter('stop', Parameter.POSITIONAL_ONLY, default=Parameter.missing),
    #:     ...     Parameter('step', Parameter.POSITIONAL_ONLY, default=Parameter.missing),
    #:     ... ])
    #:     <Signature (start[, stop[, step]], /)>
    missing = type("_missing", (), {})

    def __init__(
        self,
        name: str,
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = PARAM_EMPTY,
        annotation: Any = PARAM_EMPTY,
    ):
        """
        :param name: The parameter's name
        :param kind: The parameter's kind. See :attr:`inspect.Parameter.kind` for details.
        :param default: The parameter's default value, or one of the special values :attr:`inspect.Parameter.empty` and :attr:`Parameter.missing`
        :param annotation: The parameter's type annotation
        """
        if default is PARAM_EMPTY:
            default = inspect.Parameter.empty

        if annotation is PARAM_EMPTY:
            annotation = inspect.Parameter.empty

        super().__init__(name, kind, default=default, annotation=annotation)

    @classmethod
    def from_parameter(cls, parameter: inspect.Parameter) -> Self:
        """
        Creates a new :class:`Parameter` instance from an :class:`inspect.Parameter` instance.

        :param parameter: An :class:`inspect.Parameter` instance
        :return: A new :class:`Parameter` instance
        """
        if isinstance(parameter, cls):
            return parameter

        return cls(
            parameter.name,
            kind=parameter.kind,
            default=parameter.default,
            annotation=parameter.annotation,
        )

    @property
    def has_annotation(self) -> bool:
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
        Returns a boolean indicating whether this parameter can be omitted or
        requires an argument.

        Returns ``True`` if the parameter has a default value or is a vararg.
        """
        return self.default is not self.empty or self.is_vararg

    @property
    def has_default(self) -> bool:
        """
        Returns whether the parameter's :attr:`default` is not
        :attr:`Parameter.empty`.

        (Unlike ``is_optional``, this returns ``False`` for varargs.)
        """
        return self.default is not Parameter.empty

    def _to_string(
        self,
        implicit_typing: bool,
        brackets_and_commas: bool = True,
    ) -> str:
        text = self.name

        if self.has_annotation:
            from .typing import annotation_to_string

            ann = annotation_to_string(self.annotation, implicit_typing=implicit_typing)
            text += f": {ann}"

        if self.kind is __class__.VAR_POSITIONAL:
            text = "*" + text
        elif self.kind is __class__.VAR_KEYWORD:
            text = "**" + text

        if self.default is __class__.missing:
            if brackets_and_commas:
                text = f"[{text}]"
        elif self.default is not __class__.empty:
            if self.has_annotation:
                template = "{} = {}"
            else:
                template = "{}={}"

            default = repr(self.default)
            text = template.format(text, default)

        if brackets_and_commas:
            if self.kind is __class__.KEYWORD_ONLY:
                text = "*, " + text
            elif self.kind is __class__.POSITIONAL_ONLY:
                text = text + ", /"

        return text

    def to_string(self, implicit_typing: bool = False) -> str:
        """
        Returns a string representation of this parameter, similar to how
        parameters are written in function signatures.

        Examples::

            >>> Parameter('foo', Parameter.VAR_POSITIONAL).to_string()
            '*foo'
            >>> Parameter('foo', annotation=int, default=3).to_string()
            'foo: int = 3'

        :param implicit_typing: If ``True``, the "typing." prefix will be
            omitted from types defined in the ``typing`` module
        :return: A string representation of this parameter, like you would see
            in a function signature
        """
        return self._to_string(implicit_typing)

    def __repr__(self) -> str:
        cls_name = type(self).__qualname__
        text = self.to_string()

        return f"<{cls_name} {text}>"

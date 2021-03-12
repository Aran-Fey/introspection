
import ast
import builtins
import inspect
import os
import sys
import types
import typing
import warnings
from numbers import Number
from typing import Union, List, Dict, Callable, Any, Iterator, Iterable, Mapping, Tuple, Optional, TypeVar, ByteString, Type

from .parameter import Parameter
from .typing import annotation_to_string

__all__ = ['Signature']


T = TypeVar('T')
A = TypeVar('A')
B = TypeVar('B')
K = TypeVar('K')
V = TypeVar('V')
IntOrFloatVar = TypeVar('T', int, float)
FilePath = Union[str, bytes, os.PathLike]

BUILTIN_SIGNATURES = {
    'abs': (Any, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=typing.SupportsAbs)
    ]),
    'all': (bool, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable)
    ]),
    'any': (bool, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable)
    ]),
    'ascii': (str, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'bin': (str, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=int)
    ]),
    'bool': (bool, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'breakpoint': (None, [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('kwargs', Parameter.VAR_KEYWORD, annotation=Any)
    ]),
    'bytearray': (bytearray, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Union[str, ByteString]),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str)
    ]),
    'bytes': (bytes, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Union[str, ByteString, typing.SupportsBytes]),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str)
    ]),
    'callable': (bool, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'chr': (str, [
        Parameter('i', Parameter.POSITIONAL_ONLY, annotation=int)
    ]),
    'classmethod': (classmethod, [
        Parameter('method', Parameter.POSITIONAL_ONLY, annotation=Callable)
    ]),
    'compile': (types.CodeType, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, annotation=Union[str, ByteString, ast.AST]),
        Parameter('filename', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter('mode', Parameter.POSITIONAL_OR_KEYWORD, annotation=typing.Literal['eval', 'exec'] if hasattr(typing, 'Literal') else str),
        Parameter('flags', Parameter.POSITIONAL_OR_KEYWORD, 0, int),
        Parameter('dont_inherit', Parameter.POSITIONAL_OR_KEYWORD, False, bool),
        Parameter('optimize', Parameter.POSITIONAL_OR_KEYWORD, -1, int),
    ]),
    'complex': (complex, [
        Parameter('real', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Union[int, float]),
        Parameter('imag', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Union[int, float]),
    ]),
    'delattr': (None, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('name', Parameter.POSITIONAL_ONLY, annotation=str),
    ]),
    'dict': (Dict[K, V], [
        Parameter('mapping_or_iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Union[Mapping[K, V], Iterable[Tuple[K, V]]]),
        Parameter('kwargs', Parameter.VAR_KEYWORD, annotation=V),
    ]),
    'dir': (List[str], [
        Parameter('object', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'divmod': (Tuple[IntOrFloatVar, IntOrFloatVar], [
        Parameter('a', Parameter.POSITIONAL_ONLY, annotation=IntOrFloatVar),
        Parameter('b', Parameter.POSITIONAL_ONLY, annotation=IntOrFloatVar),
    ]),
    'enumerate': (Iterator[Tuple[int, T]], [
        Parameter('iterable', Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable[T]),
        Parameter('start', Parameter.POSITIONAL_OR_KEYWORD, 0, int),
    ]),
    'eval': (Any, [
        Parameter('expression', Parameter.POSITIONAL_ONLY, annotation=Union[str, types.CodeType]),
        Parameter('globals', Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
        Parameter('locals', Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
    ]),
    'exec': (None, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Union[str, types.CodeType]),
        Parameter('globals', Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
        Parameter('locals', Parameter.POSITIONAL_ONLY, None, annotation=Optional[dict]),
    ]),
    'filter': (Iterator[T], [
        Parameter('function', Parameter.POSITIONAL_ONLY, annotation=Callable[[T], Any]),
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable[T]),
    ]),
    'float': (float, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, typing.SupportsFloat)
    ]),
    'format': (str, [
        Parameter('value', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('format_spec', Parameter.POSITIONAL_ONLY, Parameter.missing, str),
    ]),
    'frozenset': (typing.FrozenSet[T], [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable[T])
    ]),
    'getattr': (Any, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('name', Parameter.POSITIONAL_ONLY, annotation=str),
        Parameter('default', Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
    ]),
    'globals': (dict, []),
    'hasattr': (bool, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('name', Parameter.POSITIONAL_ONLY, annotation=str),
    ]),
    'hash': (int, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
    ]),
    'help': (None, [
        Parameter('object', Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
    ]),
    'hex': (str, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=int)
    ]),
    'id': (int, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'input': (str, [
        Parameter('prompt', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'int': (int, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Union[str, ByteString, typing.SupportsInt]),
        Parameter('base', Parameter.POSITIONAL_ONLY, 10, int)
    ]),
    'isinstance': (bool, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('classinfo', Parameter.POSITIONAL_ONLY, annotation=Union[type, Tuple[type]])
    ]),
    'issubclass': (bool, [
        Parameter('class', Parameter.POSITIONAL_ONLY, annotation=type),
        Parameter('classinfo', Parameter.POSITIONAL_ONLY, annotation=Union[type, Tuple[type]])
    ]),
    'iter': (Iterator[T], [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Union[Iterable[T], Callable[[], T]]),
        Parameter('sentinel', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'len': (int, [
        Parameter('s', Parameter.POSITIONAL_ONLY, annotation=typing.Sized)
    ]),
    'list': (List[T], [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable[T])
    ]),
    'locals': (dict, []),
    'map': (Iterator[T], [
        Parameter('function', Parameter.POSITIONAL_ONLY, annotation=Callable[..., T]),
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Iterable)
    ]),
    'max': (Union[A, B], [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Union[A, Iterable[A]]),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Optional[Callable[[A], Any]]),
        Parameter('default', Parameter.KEYWORD_ONLY, Parameter.missing, B)
    ]),
    'memoryview': (memoryview, [
        Parameter('obj', Parameter.POSITIONAL_ONLY, annotation=ByteString)
    ]),
    'min': (Union[A, B], [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Union[A, Iterable[A]]),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Optional[Callable[[A], Any]]),
        Parameter('default', Parameter.KEYWORD_ONLY, Parameter.missing, B)
    ]),
    'next': (Union[A, B], [
        Parameter('iterator', Parameter.POSITIONAL_ONLY, annotation=Iterator[A]),
        Parameter('default', Parameter.POSITIONAL_ONLY, Parameter.missing, B)
    ]),
    'object': (object, []),
    'oct': (str, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=int)
    ]),
    'open': (typing.IO, [
        Parameter('file', Parameter.POSITIONAL_ONLY, annotation=FilePath),
        Parameter('mode', Parameter.POSITIONAL_OR_KEYWORD, 'r', str),
        Parameter('buffering', Parameter.POSITIONAL_OR_KEYWORD, -1, int),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('newline', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[str]),
        Parameter('closefd', Parameter.POSITIONAL_OR_KEYWORD, True, bool),
        Parameter('opener', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[FilePath, int], typing.IO]]),
    ]),
    'ord': (int, [
        Parameter('c', Parameter.POSITIONAL_ONLY, annotation=str)
    ]),
    'pow': (Number, [
        Parameter('base', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('exp', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('mod', Parameter.POSITIONAL_ONLY, Parameter.missing, Number),
    ]) if sys.version_info < (3, 8) else (Number, [
        Parameter('base', Parameter.POSITIONAL_OR_KEYWORD, annotation=Number),
        Parameter('exp', Parameter.POSITIONAL_OR_KEYWORD, annotation=Number),
        Parameter('mod', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, Number),
    ]),
    'print': (None, [
        Parameter('objects', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('sep', Parameter.KEYWORD_ONLY, ' ', Optional[str]),
        Parameter('end', Parameter.KEYWORD_ONLY, '\n', Optional[str]),
        Parameter('file', Parameter.KEYWORD_ONLY, sys.stdout, typing.TextIO),
        Parameter('flush', Parameter.KEYWORD_ONLY, False, bool),
    ]),
    'property': (property, [
        Parameter('fget', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[A], B]]),
        Parameter('fset', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[A, B], Any]]),
        Parameter('fdel', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[A], Any]]),
        Parameter('doc', Parameter.POSITIONAL_OR_KEYWORD, None, str),
    ]),
    'range': (range, [
        Parameter('start_or_stop', Parameter.POSITIONAL_ONLY, annotation=int),
        Parameter('stop', Parameter.POSITIONAL_ONLY, Parameter.missing, int),
        Parameter('step', Parameter.POSITIONAL_ONLY, Parameter.missing, int)
    ]),
    'repr': (str, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'reversed': (Iterator[T], [
        Parameter('seq', Parameter.POSITIONAL_ONLY, annotation=typing.Reversible[T])
    ]),
    'round': (Number, [
        Parameter('number', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('ndigits', Parameter.POSITIONAL_ONLY, Parameter.missing, int),
    ]),
    'set': (typing.Set[T], [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable[T])
    ]),
    'setattr': (None, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('name', Parameter.POSITIONAL_ONLY, annotation=str),
        Parameter('value', Parameter.POSITIONAL_ONLY, annotation=Any),
    ]),
    'slice': (slice, [
        Parameter('start_or_stop', Parameter.POSITIONAL_ONLY, annotation=int),
        Parameter('stop', Parameter.POSITIONAL_ONLY, Parameter.missing, int),
        Parameter('step', Parameter.POSITIONAL_ONLY, Parameter.missing, int)
    ]),
    'sorted': (List[T], [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable[T]),
        Parameter('key', Parameter.KEYWORD_ONLY, None, Optional[Callable[[T], Any]]),
        Parameter('reverse', Parameter.KEYWORD_ONLY, False, bool),
    ]),
    'staticmethod': (staticmethod, [
        Parameter('method', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'str': (str, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, 'utf-8', str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, 'strict', str),
    ]),
    'sum': (Any, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable),
        Parameter('start', Parameter.POSITIONAL_ONLY, 0, Any),
    ]) if sys.version_info < (3, 8) else (Any, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable),
        Parameter('start', Parameter.POSITIONAL_OR_KEYWORD, 0, Any),
    ]),
    'super': (super, [
        Parameter('type', Parameter.POSITIONAL_ONLY, Parameter.missing, type),
        Parameter('object_or_type', Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
    ]),
    'tuple': (tuple, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable)
    ]),
    'type': (type, [
        Parameter('object_or_name', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('bases', Parameter.POSITIONAL_ONLY, Parameter.missing, Tuple[type]),
        Parameter('dict', Parameter.POSITIONAL_ONLY, Parameter.missing, dict),
    ]),
    'vars': (dict, [
        Parameter('object', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'zip': (Iterator[tuple], [
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Iterable)
    ]),
    '__import__': (types.ModuleType, [
        Parameter('name', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter('globals', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[dict]),
        Parameter('locals', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[dict]),
        Parameter('fromlist', Parameter.POSITIONAL_OR_KEYWORD, (), Iterable),
        Parameter('level', Parameter.POSITIONAL_OR_KEYWORD, 0, int),
    ]),
    '__build_class__': (type, [
        Parameter('func', Parameter.POSITIONAL_OR_KEYWORD, annotation=Callable),
        Parameter('name', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter('bases', Parameter.VAR_POSITIONAL, annotation=type),
        Parameter('metaclass', Parameter.KEYWORD_ONLY, None, Optional[Callable[[str, Tuple[type], dict], type]]),
        Parameter('kwds', Parameter.VAR_KEYWORD, annotation=Any),
    ]),
}
for key in list(BUILTIN_SIGNATURES):
    value = BUILTIN_SIGNATURES.pop(key)

    try:
        key = getattr(builtins, key)
    except AttributeError:
        continue

    BUILTIN_SIGNATURES[key] = value


class Signature(inspect.Signature):
    """
    An :class:`inspect.Signature` subclass that represents a function's parameter signature and return annotation.

    Instances of this class are immutable.

    :ivar parameters: An :class:`OrderedDict` of :class:`Parameter` objects
    :ivar return_annotation: The annotation for the function's return value
    """
    __slots__ = ()

    def __init__(self,
                 parameters: Union[Iterable[Parameter], Dict[str, Parameter], None] = None,
                 return_annotation: Any = inspect.Signature.empty,
                 validate_parameters: bool = True,
                 ):
        """
        :param parameters: A list or dict of :class:`Parameter` objects
        :param return_annotation: The annotation for the function's return value
        """
        super().__init__(
            parameters,
            return_annotation=return_annotation,
            __validate_parameters__=validate_parameters
        )

    @classmethod
    def from_signature(cls, signature: inspect.Signature, parameter_type: type = Parameter, *, param_type=None) -> 'Signature':
        """
        Creates a new ``Signature`` instance from an :class:`inspect.Signature` instance.
        
        .. deprecated:: 1.2
           The ``param_type`` parameter. Use ``parameter_type`` instead.

        :param signature: An :class:`inspect.Signature` instance
        :param parameter_type: The class to use for the signature's parameters
        :return: A new ``Signature`` instance
        """
        if param_type is not None:
            warnings.warn("The 'param_type' parameter is deprecated; use 'parameter_type' instead", DeprecationWarning)
            parameter_type = param_type
        
        params = [
            parameter_type.from_parameter(param)
            for param in signature.parameters.values()
        ]
        return cls(params, return_annotation=signature.return_annotation)

    @classmethod
    def from_callable(cls,
                      callable_: Callable,
                      parameter_type: Type[Parameter] = Parameter,
                      follow_wrapped: bool = True,
                      use_signature_db: bool = True,
                      *,
                      param_type=None,
                      ) -> 'Signature':
        """
        Returns a matching :class:`Signature` instance for the given ``callable_``.
        
        Because the signatures of builtin functions often cannot be determined
        (at least in older python versions), this function contains a database
        of signatures for builtin functions. These signatures contain much more
        detail than :func:`inspect.signature` would provide - like type annotations
        and default values of :attr:`Parameter.missing`.
        
        Pass ``use_signature_db=False`` if you wish to bypass the signature
        database.

        .. versionchanged:: 1.1
           Returns more accurate signatures for builtin functions.
           Also added missing "value" parameter for ``setattr``.
        
        .. versionadded:: 1.2
           Added ``use_signature_db`` parameter.
        
        .. versionchanged:: 1.2
           Signature database updated for python 3.9.
        
        .. deprecated:: 1.2
           The ``param_type`` parameter. Use ``parameter_type`` instead.

        :param callable_: A function or any other callable object
        :param parameter_type: The class to use for the signature's parameters
        :param follow_wrapped: Whether to unwrap decorated callables
        :param use_signature_db: Whether to look up the signature
        :return: A corresponding ``Signature`` instance
        :raises TypeError: If ``callable_`` isn't a callable object
        :raises ValueError: If the signature can't be determined (can happen for functions defined in C extensions)
        """
        if param_type is not None:
            warnings.warn("The 'param_type' parameter is deprecated; use 'parameter_type' instead", DeprecationWarning)
            parameter_type = param_type
        
        if follow_wrapped:
            while hasattr(callable_, '__wrapped__'):
                callable_ = callable_.__wrapped__

        if not callable(callable_):
            raise TypeError("Expected a callable, not {!r}".format(callable_))

        if use_signature_db and callable_ in BUILTIN_SIGNATURES:
            ret_type, params = BUILTIN_SIGNATURES[callable_]
            params = [parameter_type.from_parameter(param) for param in params]
            return cls(params, ret_type)

        try:
            sig = inspect.signature(callable_, follow_wrapped=False)
        except ValueError:  # callables written in C don't have an accessible signature
            pass
        else:
            return cls.from_signature(sig, parameter_type=parameter_type)

        # builtin exceptions also need special handling, but we don't want to hard-code
        # all of them in BUILTIN_SIGNATURES
        if isinstance(callable_, type) and issubclass(callable_, BaseException):
            return cls([
                parameter_type('args', Parameter.VAR_POSITIONAL),
                parameter_type('kwargs', Parameter.VAR_KEYWORD),
            ])

        raise ValueError("Can't determine signature of {}".format(callable_))

    def without_parameters(self, *params_to_remove) -> 'Signature':
        """
        Returns a copy of this signature with some parameters removed.

        Parameters can be referenced by their name or index.

        Example::

            >>> sig = Signature([
            ...     Parameter('foo'),
            ...     Parameter('bar'),
            ...     Parameter('baz')
            ... ])
            >>> sig.without_parameters(0, 'baz')
            <Signature (bar)>

        :param parameters: Names or indices of the parameters to remove
        :return: A copy of this signature without the given parameters
        """
        params_to_remove = set(params_to_remove)

        parameters = []

        for i, param in enumerate(self.parameters.values()):
            if i in params_to_remove or param.name in params_to_remove:
                continue

            parameters.append(param)

        return self.replace(parameters=parameters)

    @property
    def param_list(self):
        """
        Returns a list of the signature's parameters.
        
        .. deprecated:: 1.2
           Use :attr:`parameter_list` instead.
        """
        warnings.warn("The 'param_list' property is deprecated; use 'parameter_list' instead", DeprecationWarning)
        return self.parameter_list
    
    @property
    def parameter_list(self):
        """
        Returns a list of the signature's parameters.
        """
        return list(self.parameters.values())

    @property
    def has_return_annotation(self):
        """
        Returns whether the signature's return annotation is not :attr:`Signature.empty`.
        """
        return self.return_annotation is not Signature.empty

    @property
    def num_required_arguments(self):
        """
        Returns the number of required arguments, i.e. arguments with no default value.
        """
        return sum(not p.is_optional for p in self.parameters.values())

    def to_string(self, implicit_typing=False) -> str:
        """
        Returns a string representation of this signature.

        Example::

            >>> Signature([
            ...    Parameter('nums', Parameter.VAR_POSITIONAL, annotation=int)
            ... ], return_annotation=int).to_string()
            '(*nums: int) -> int'
        
        :param implicit_typing: If ``True``, the "typing." prefix will be omitted from types defined in the ``typing`` module
        :return: A string representation of this signature, like you would see in python code
        """
        # Because parameters with a default of Parameter.missing have a special bracket
        # notation (like "[a[, b]]" for positional-only parameters and "[a][, b]" otherwise),
        # we'll do this in 2 steps:
        # 1) Create a list that contains 2 kinds of elements:
        #     parameters = regular parameters, separated by ", "
        #     lists of parameters = a sequence of parameters that needs to be enclosed in (nested) brackets
        # 2) Join the list with the appropriate separator for each element

        # Step 1
        param_list = list(self.parameters.values())
        num_params = len(param_list)
        param_specs = []
        i = 0

        while i < num_params:
            param = param_list[i]

            # Check if this parameter goes in square brackets
            if param.default is Parameter.missing:
                group = [param]

                # Group sequences of positional-only bracket parameters
                if param.kind is Parameter.POSITIONAL_ONLY:
                    while True:
                        i += 1
                        if i >= num_params:
                            break

                        param = param_list[i]

                        if (param.kind is not Parameter.POSITIONAL_ONLY or
                           param.default is not Parameter.missing):
                            break

                        group.append(param)

                    i -= 1

                param_specs.append(group)
            else:
                param_specs.append(param)

            i += 1

        # Step 2
        chunks = []
        is_first = True
        for i, param_spec in enumerate(param_specs):
            # insert "*" if necessary
            first_param = param_spec[0] if isinstance(param_spec, list) else param_spec
            if first_param.kind is Parameter.KEYWORD_ONLY:
                if i == 0:
                    prev_param = None
                else:
                    prev_param = param_specs[i-1]
                    if isinstance(prev_param, list):
                        prev_param = prev_param[-1]

                if (prev_param is None or
                   prev_param.kind not in {
                            Parameter.KEYWORD_ONLY,
                            Parameter.VAR_POSITIONAL
                   }):
                    if is_first:
                        chunks.append('*')
                        is_first = False
                    else:
                        chunks.append(', *')

            # If its a regular parameter, the separator is ", "
            if isinstance(param_spec, inspect.Parameter):
                if not is_first:
                    chunks.append(', ')

                chunk = param_spec._to_string_no_brackets(implicit_typing)
            # otherwise, it's a group of bracket parameters
            else:
                chunk = [
                    param._to_string_no_brackets(implicit_typing)
                    for param in param_spec
                ]
                chunk = '[, '.join(chunk) + ']'*(len(chunk)-1)

                if is_first:
                    template = '[{}]'
                else:
                    template = '[, {}]'
                chunk = template.format(chunk)

            chunks.append(chunk)

            # insert "/" if necessary
            last_param = param_spec[-1] if isinstance(param_spec, list) else param_spec
            if last_param.kind is Parameter.POSITIONAL_ONLY:
                if i == len(param_specs)-1:
                    next_param = None
                else:
                    next_param = param_specs[i+1]
                    if isinstance(next_param, list):
                        next_param = next_param[0]

                if (next_param is None or
                   next_param.kind is not Parameter.POSITIONAL_ONLY):
                    chunks.append(', /')

            is_first = False

        params = ''.join(chunks)
        # Parameter list complete

        if self.has_return_annotation:
            ann = annotation_to_string(self.return_annotation, implicit_typing)
            ann = ' -> {}'.format(ann)
        else:
            ann = ''

        return '({}){}'.format(params, ann)

    def __repr__(self):
        cls_name = type(self).__name__
        text = self.to_string()

        return '<{} {}>'.format(cls_name, text)

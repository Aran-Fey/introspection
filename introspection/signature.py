
import ast
import builtins
import inspect
import functools
import os
import re
import sys
import types
import typing
from numbers import Number
from typing import Union, List, Dict, Callable, Any, Iterator, Iterable, Tuple, Optional, TypeVar

from .parameter import Parameter
from .misc import annotation_to_string

__all__ = ['Signature', 'signature']


T = TypeVar('T')
A = TypeVar('A')
B = TypeVar('B')
K = TypeVar('K')
V = TypeVar('V')

BUILTIN_SIGNATURES = {
    'abs': (Any, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=Any)
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
    'bin': (int, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'bool': (bool, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'breakpoint': (None, [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('kwargs', Parameter.VAR_KEYWORD, annotation=Any)
    ]),
    'bytearray': (bytearray, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str)
    ]),
    'bytes': (bytes, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
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
        Parameter('method', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'compile': (types.CodeType, [
        Parameter('source', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter('filename', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter('mode', Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
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
        Parameter('mapping_or_iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable[Tuple[K, V]]),
        Parameter('kwargs', Parameter.VAR_KEYWORD, annotation=V),
    ]),
    'dir': (List[str], [
        Parameter('object', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'divmod': (Tuple[Union[int, float], Union[int, float]], [
        Parameter('a', Parameter.POSITIONAL_ONLY, annotation=Union[int, float]),
        Parameter('b', Parameter.POSITIONAL_ONLY, annotation=Union[int, float]),
    ]),
    'enumerate': (Iterator[Tuple[int, T]], [
        Parameter('iterable', Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable[T]),
        Parameter('start', Parameter.POSITIONAL_OR_KEYWORD, 1, int),
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
        Parameter('prompt', Parameter.POSITIONAL_ONLY, Parameter.missing, str)
    ]),
    'int': (int, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Union[str, typing.SupportsInt]),
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
    'map': (Iterator, [
        Parameter('function', Parameter.POSITIONAL_ONLY, annotation=Callable),
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Iterable)
    ]),
    'max': (Union[A, B], [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=A),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Callable[[A], Any]),
        Parameter('default', Parameter.KEYWORD_ONLY, Parameter.missing, B)
    ]),
    'memoryview': (memoryview, [
        Parameter('obj', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'min': (Union[A, B], [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=A),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Callable[[A], Any]),
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
        Parameter('file', Parameter.POSITIONAL_ONLY, annotation=Union[str, bytes, os.PathLike]),
        Parameter('mode', Parameter.POSITIONAL_OR_KEYWORD, 'r', str),
        Parameter('buffering', Parameter.POSITIONAL_OR_KEYWORD, -1, int),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('newline', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[str]),
        Parameter('closefd', Parameter.POSITIONAL_OR_KEYWORD, True, bool),
        Parameter('opener', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[Union[str, bytes, os.PathLike], int], typing.IO]]),
    ]),
    'ord': (int, [
        Parameter('c', Parameter.POSITIONAL_ONLY, annotation=str)
    ]),
    'pow': (Number, [
        Parameter('base', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('exp', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('mod', Parameter.POSITIONAL_ONLY, Parameter.missing, Number),
    ]),
    'print': (None, [
        Parameter('objects', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('sep', Parameter.KEYWORD_ONLY, ' ', str),
        Parameter('end', Parameter.KEYWORD_ONLY, '\n', str),
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
        Parameter('start', Parameter.KEYWORD_ONLY, 0, Any),
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
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Iterable[Any])
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
    """
    __slots__ = ()

    def __init__(self,
                 parameters: Union[List[Parameter], Dict[str, Parameter], None] = None,
                 return_annotation: object = inspect.Signature.empty,
                 validate_parameters: bool = True,
                 ):
        super().__init__(
            parameters,
            return_annotation=return_annotation,
            __validate_parameters__=validate_parameters
        )

    @classmethod
    def from_signature(cls, signature: inspect.Signature, param_type: type = Parameter) -> 'Signature':
        """
        Creates a new `Signature` instance from an :class:`inspect.Signature` instance.

        :param signature: An :class:`inspect.Signature` instance
        :param param_type: The class to use for the signature's parameters
        :return: A new :class:`Signature` instance
        """
        params = [param_type.from_parameter(param) for param in signature.parameters.values()]
        return cls(params, return_annotation=signature.return_annotation)

    @classmethod
    def from_callable(cls,
                      callable_: Callable,
                      param_type: type = Parameter,
                      follow_wrapped: bool = True,
                      ) -> 'Signature':
        """
        Returns a matching `Signature` instance for the given *callable_*.

        :param callable_: A function or any other callable object
        :param param_type: The class to use for the signature's parameters
        :param follow_wrapped: Whether to unwrap decorated callables
        :return: A corresponding `Signature` instance
        :raises:
            TypeError: If ``callable_`` isn't a callable
            ValueError: If the signature can't be determined (can happen for functions defined in C extensions)
        """

        if follow_wrapped:
            while hasattr(callable_, '__wrapped__'):
                callable_ = callable_.__wrapped__

        if not callable(callable_):
            raise TypeError("Expected a callable, not {!r}".format(callable_))

        if callable_ in BUILTIN_SIGNATURES:
            ret_type, params = BUILTIN_SIGNATURES[callable_]
            params = [param_type.from_parameter(param) for param in params]
            return cls(params, ret_type)
        
        try:
            sig = inspect.signature(callable_, follow_wrapped=False)
        except ValueError:  # callables written in C don't have an accessible signature
            pass
        else:
            return cls.from_signature(sig, param_type=param_type)
        
        # builtin exceptions also need special handling, but we don't want to hard-code
        # all of them in BUILTIN_SIGNATURES
        if isinstance(callable_, type) and issubclass(callable_, BaseException):
            return cls([
                param_type('args', Parameter.VAR_POSITIONAL),
                param_type('kwargs', Parameter.VAR_KEYWORD),
            ])

        doc = callable_.__doc__
        if doc:
            try:
                return cls.from_docstring(doc, param_type=param_type)
            except ValueError:
                pass

        raise ValueError("Can't determine signature of {}".format(callable_))

    @classmethod
    def from_class(cls, class_):
        return cls.from_callable(class_)

    @property
    def has_return_annotation(self):
        """
        Returns whether the signature's return annotation is not :attr:`Signature.empty`.
        """
        return self.return_annotation is not Signature.empty

    @property
    def num_required_arguments(self):
        """
        Returns the number of required arguments, i.e. arguments with a default value.
        """
        return sum(not p.is_optional for p in self)

    def __iter__(self):
        return iter(self.parameters.values())

    def union(self, *signatures):
        """
        Merges multiple signatures into one, in such a way that any
        set of arguments accepted by one of the input signatures is
        also accepted by the resulting signature.
        
        Example::
        
            >>> sig1
            <Signature (a) -> int>
            >>> sig2
            <Signature (*, b=3) -> float>
            >>> sig1.merged_with(sig2)
            <Signature (a, *, b=3) -> Union[int, float]>
        
        :param signatures:
        :return:
        """
        def merge_types(types_):
            types_ = set(types_)
            
            if len(types_) == 1:
                return types_.pop()
            
            # split the types into classes and stuff from the typing module
            classes = set()
            annotations = set()
            
            for type_ in types_:
                if type_.__module__ == 'typing':
                    annotations.add(type_)
                else:
                    classes.add(type_)
            
            # if any class is a subclass of another, remove it
            classes_ = set()
            while classes:
                cls = classes.pop()
                
                if not issubclass(cls, tuple(classes)):
                    classes_.add(cls)
            
            # TODO: do the same thing for typing annotations, e.g. filter out List[X] if list or List is present
            
            types_ = tuple(classes | annotations)
            
            if len(types_) == 1:
                return types_[0]
            else:
                return typing.Union[types_]
        
        # merge parameters
        params = []
        # FIXME

        # merge return annotations
        return_annotations = [
            sig.return_annotation for sig in signatures
            if sig.has_return_annotation
        ]
        if return_annotations:
            return_annotation = merge_types(return_annotations)
        else:
            return_annotation = Signature.empty

        cls = type(self)
        return cls(params, return_annotation=return_annotation)

    def to_string(self):
        param_list = list(self.parameters.values())
        chunks = []
        i = len(param_list) - 1
        while i >= 0:
            param = param_list[i]
            
            text = param._to_string_no_brackets()
            
            if i > 0:
                text = ', ' + text
            
            if param.default is Parameter.missing:
                text = '[{}]'.format(text)
            
                # these need special attention because their representation is nested, like e.g. [a[, b]]
                if param.kind is Parameter.POSITIONAL_ONLY:
                    while i > 0 and param_list[i-1].default is Parameter.missing:
                        i -= 1
                        
                        param = param_list[i]
                        t = param._to_string_no_brackets()
                        
                        if i > 0:
                            t = ', ' + t
                        
                        text = '[{}{}]'.format(t, text)
            
            chunks.append(text)
            i -= 1
        
        chunks.reverse()
        params = ''.join(chunks)
        
        if self.has_return_annotation:
            ann = annotation_to_string(self.return_annotation)
            ann = ' -> {}'.format(ann)
        else:
            ann = ''
        
        return '({}){}'.format(params, ann)
    
    def __repr__(self):
        cls_name = type(self).__name__
        text = self.to_string()
        
        return '<{} {}>'.format(cls_name, text)


@functools.wraps(Signature.from_callable)
def signature(*args, **kwargs):
    """
    Shorthand for ``Signature.from_callable``.
    """
    return Signature.from_callable(*args, **kwargs)

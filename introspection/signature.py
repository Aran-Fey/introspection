
import ast
import builtins
import inspect
import io
import functools
import os
import re
import sys
import types
import typing
from numbers import Number
from typing import Union, List, Dict, Callable, Any, Iterator, Iterable, Tuple, Optional

from .parameter import Parameter
from .misc import common_ancestor

__all__ = ['Signature', 'signature']


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
        Parameter('real', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, int),
        Parameter('imag', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, int),
    ]),
    'delattr': (None, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('name', Parameter.POSITIONAL_ONLY, annotation=str),
    ]),
    'dict': (dict, [
        Parameter('mapping_or_iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable),
        Parameter('kwargs', Parameter.VAR_KEYWORD, annotation=Any),
    ]),
    'dir': (List[str], [
        Parameter('object', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'divmod': (Tuple[int, int], [
        Parameter('a', Parameter.POSITIONAL_ONLY, annotation=Union[int, float]),
        Parameter('b', Parameter.POSITIONAL_ONLY, annotation=Union[int, float]),
    ]),
    'enumerate': (Iterator[Tuple[int, Any]], [
        Parameter('iterable', Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable),
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
    'filter': (Iterator, [
        Parameter('function', Parameter.POSITIONAL_ONLY, annotation=Callable[[Any], Any]),
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable),
    ]),
    'float': (float, [
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'format': (str, [
        Parameter('value', Parameter.POSITIONAL_ONLY, annotation=Any),
        Parameter('format_spec', Parameter.POSITIONAL_ONLY, Parameter.missing, str),
    ]),
    'frozenset': (frozenset, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable)
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
        Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, Any),
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
    'iter': (Iterator, [
        Parameter('object', Parameter.POSITIONAL_ONLY, annotation=Union[Iterable, Callable[[], Any]]),
        Parameter('sentinel', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'len': (int, [
        Parameter('s', Parameter.POSITIONAL_ONLY, annotation=typing.Sized)
    ]),
    'list': (list, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable)
    ]),
    'locals': (dict, []),
    'map': (Iterator, [
        Parameter('function', Parameter.POSITIONAL_ONLY, annotation=Callable),
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Iterable)
    ]),
    'max': (Any, [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Callable[[Any], Any]),
        Parameter('default', Parameter.KEYWORD_ONLY, Parameter.missing, Any)
    ]),
    'memoryview': (memoryview, [
        Parameter('obj', Parameter.POSITIONAL_ONLY, annotation=Any)
    ]),
    'min': (Any, [
        Parameter('args', Parameter.VAR_POSITIONAL, annotation=Any),
        Parameter('key', Parameter.KEYWORD_ONLY, Parameter.missing, Callable[[Any], Any]),
        Parameter('default', Parameter.KEYWORD_ONLY, Parameter.missing, Any)
    ]),
    'next': (Any, [
        Parameter('iterator', Parameter.POSITIONAL_ONLY, annotation=Iterator),
        Parameter('default', Parameter.POSITIONAL_ONLY, Parameter.missing, Any)
    ]),
    'object': (object, []),
    'oct': (str, [
        Parameter('x', Parameter.POSITIONAL_ONLY, annotation=int)
    ]),
    'open': (io.IOBase, [
        Parameter('file', Parameter.POSITIONAL_ONLY, annotation=Union[str, bytes, os.PathLike]),
        Parameter('mode', Parameter.POSITIONAL_OR_KEYWORD, 'r', str),
        Parameter('buffering', Parameter.POSITIONAL_OR_KEYWORD, -1, int),
        Parameter('encoding', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('errors', Parameter.POSITIONAL_OR_KEYWORD, Parameter.missing, str),
        Parameter('newline', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[str]),
        Parameter('closefd', Parameter.POSITIONAL_OR_KEYWORD, True, bool),
        Parameter('opener', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[Union[str, bytes, os.PathLike], int], io.IOBase]]),
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
        Parameter('file', Parameter.KEYWORD_ONLY, sys.stdout, io.IOBase),
        Parameter('flush', Parameter.KEYWORD_ONLY, False, bool),
    ]),
    'property': (property, [
        Parameter('fget', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[Any], Any]]),
        Parameter('fset', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[Any, Any], Any]]),
        Parameter('fdel', Parameter.POSITIONAL_OR_KEYWORD, None, Optional[Callable[[Any], Any]]),
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
    'reversed': (Iterator, [
        Parameter('seq', Parameter.POSITIONAL_ONLY, annotation=typing.Reversible)
    ]),
    'round': (Number, [
        Parameter('number', Parameter.POSITIONAL_ONLY, annotation=Number),
        Parameter('ndigits', Parameter.POSITIONAL_ONLY, Parameter.missing, int),
    ]),
    'set': (set, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, Parameter.missing, Iterable)
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
    'sorted': (list, [
        Parameter('iterable', Parameter.POSITIONAL_ONLY, annotation=Iterable),
        Parameter('key', Parameter.KEYWORD_ONLY, None, Optional[Callable[[Any], Any]]),
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
        Parameter('iterables', Parameter.VAR_POSITIONAL, annotation=Any)
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
    @functools.lru_cache()
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
        except ValueError:  # builtin types don't have an accessible signature
            pass
        else:
            return cls.from_signature(sig, param_type=param_type)

        doc = callable_.__doc__
        if doc:
            return cls.from_docstring(doc, param_type=param_type)

        raise ValueError("Can't determine signature of {}".format(callable_))

    @classmethod
    def from_docstring(cls, doc, param_type=Parameter):
        TYPE_MAP = {
            'object': object,
            'dict': dict,
            'dictionary': dict,
            'list': list,
            'tuple': tuple,
            'set': set,
            'str': str,
            'bytes': bytes,
            'text': str,
            'int': int,
            'integer': int,
            'float': float,
            'complex': complex,
            'bool': bool,
            'boolean': bool,
            'range object': range,
            'class': type,
            'metaclass': Callable[[str, Tuple[type], dict], type],
        }

        pattern = re.compile(r'[\w.]+\((.*)\)(?: -> (.+))?')

        params = []
        return_types = set()
        for line_nr, line in enumerate(doc.strip().splitlines()):
            match = pattern.match(line)
            if not match:
                break

            return_type = match.group(2)
            if return_type is None:
                return_types.add(object)
            else:
                try:
                    return_type = TYPE_MAP[return_type]
                except KeyError:
                    pass
                else:
                    return_types.add(return_type)

            paramlist = match.group(1)
            paramlist = paramlist.replace('[, ', ', [')
            param_kind = Parameter.POSITIONAL_OR_KEYWORD
            for i, param_desc in enumerate(paramlist.split(', ')):
                if param_desc == '/':
                    for param in params[:i]:
                        param['kind'] = Parameter.POSITIONAL_ONLY
                    continue
                elif param_desc == '*':
                    param_kind = Parameter.KEYWORD_ONLY
                    continue

                try:
                    param = params[i]
                except IndexError:
                    param = {
                        'names': set(),
                        'defaults': [],
                        'types': set(),
                        'kind': param_kind
                    }
                    params.append(param)

                    # if there's a form with fewer arguments, then this
                    # parameter must be optional
                    if line_nr > 0:
                        param['defaults'].append(Parameter.missing)

                name, _, default = param_desc.partition('=')

                # a name in square brackets means it's optional
                if name.startswith('['):
                    name = name[1:-1]
                    default = Parameter.missing
                # a name starting with * or ** means it's a vararg
                elif name.startswith('**'):
                    name = name[2:]
                    # var-kwargs must actually be listed last, but
                    # we'll let it slide and treat subsequent
                    # parameters as keyword-only
                    param['kind'] = Parameter.VAR_KEYWORD
                    param_kind = Parameter.KEYWORD_ONLY
                elif name.startswith('*'):
                    name = name[1:]
                    param['kind'] = Parameter.VAR_POSITIONAL
                    param_kind = Parameter.KEYWORD_ONLY

                param['names'].add(name)

                if default is Parameter.missing:
                    annotation = object
                elif default:
                    default = ast.literal_eval(default)
                    annotation = type(default)
                else:
                    default = Parameter.empty
                    annotation = TYPE_MAP.get(name, object)
                param['defaults'].append(default)
                param['types'].add(annotation)

        parameters = []
        for param in params:
            if len(param['names']) == 1:
                name = next(iter(param['names']))
                kind = param['kind']
            else:
                name = '_or_'.join(sorted(param['names']))
                kind = Parameter.POSITIONAL_ONLY

            defaults = []
            for value in param['defaults']:
                if value not in defaults:
                    defaults.append(value)
            if len(defaults) == 1:
                default = defaults[0]
            else:
                default = Parameter.missing

            annotation = common_ancestor(param['types'])

            parameter = param_type(name, kind, default, annotation)
            parameters.append(parameter)

        return_annotation = common_ancestor(return_types)

        return cls(parameters, return_annotation=return_annotation)

    @classmethod
    def from_class(cls, class_):
        """

        :param class_:
        :return:
        """
        return cls.from_callable(class_)

    @property
    def has_return_annotation(self):
        return self.return_annotation is not Signature.empty

    @property
    def num_required_arguments(self):
        return sum(not p.is_optional for p in self)

    def __iter__(self):
        return iter(self.parameters.values())

    def merged_with(self, *signatures):
        """
        Merges multiple signatures into one, in such a way that
        the resulting signature #FIXME

        :param signatures:
        :return:
        """
        # merge parameters
        params = []
        

        # merge return annotations
        return_annotations = [
            sig.return_annotation for sig in signatures
            if sig.has_return_annotation
        ]
        if return_annotations:
            return_annotation = common_ancestor(return_annotations)
        else:
            return_annotation = Signature.empty

        cls = type(self)
        return cls(params, return_annotation=return_annotation)


@functools.wraps(Signature.from_callable)
def signature(*args, **kwargs):
    return Signature.from_callable(*args, **kwargs)

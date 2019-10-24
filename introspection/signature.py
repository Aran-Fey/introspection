
import ast
import inspect
import functools
import re
from typing import Union, List, Dict, Callable

from .parameter import Parameter
from .misc import common_ancestor

__all__ = ['Signature', 'signature']


BUILTIN_SIGNATURES = {
    bool: (bool, [Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, object)]),
    float: (float, [Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, object)]),
    int: (int, [Parameter('x', Parameter.POSITIONAL_ONLY, Parameter.missing, object),
                Parameter('base', Parameter.POSITIONAL_ONLY, 10, int)]),
}


class Signature(inspect.Signature):
    """
    An :class:`inspect.Signature` subclass that represents a function's parameter signature and return annotation.

    :ivar parameters: An :class:`OrderedDict` of parameter names mapped to :class:`Parameter` instances
    :ivar return_annotation: The annotation for the return value, or *Signature.empty*
    """

    empty = inspect.Signature.empty

    def __init__(self,
                 parameters: Union[List[Parameter], Dict[str, Parameter], None] = None,
                 return_annotation: object = empty):  # FIXME: figure out why sphinx-autodoc messes up these default values
        super().__init__(parameters, return_annotation=return_annotation, __validate_parameters__=False)

    @classmethod
    def from_signature(cls, signature: inspect.Signature, parameter_type=Parameter) -> 'Signature':
        """
        Creates a new `Signature` instance from an :class:`inspect.Signature` instance.

        :param signature: An :class:`inspect.Signature` instance
        :return: A new `Signature` instance
        """
        params = [parameter_type.from_parameter(param) for param in signature.parameters.values()]
        return cls(params, return_annotation=signature.return_annotation)

    @classmethod
    @functools.lru_cache()
    def from_callable(cls, callable_: Callable, parameter_type=Parameter) -> 'Signature':
        """
        Returns a matching `Signature` instance for the given *callable_*.

        :param callable_: A function or any other callable object
        :return: A corresponding `Signature` instance
        """

        if callable_ in BUILTIN_SIGNATURES:
            ret_type, params = BUILTIN_SIGNATURES[callable_]
            params = [parameter_type.from_parameter(param) for param in params]
            return cls(params, ret_type)

        try:
            sig = inspect.signature(callable_)
        except ValueError:  # builtin types don't have an accessible signature
            pass
        else:
            return cls.from_signature(sig, parameter_type=parameter_type)

        doc = callable_.__doc__
        if doc:
            return cls.from_docstring(doc, parameter_type=parameter_type)

        raise TypeError("Can't determine signature of {}".format(callable_))

    @classmethod
    def from_docstring(cls, doc, parameter_type=Parameter):
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
        }

        pattern = re.compile(r'[\w.]+\((.*)\)(?: -> (.+))?')

        params = []
        return_types = set()
        for line_nr, line in enumerate(doc.splitlines()):
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
            kw_only = False
            for i, param_desc in enumerate(paramlist.split(', ')):
                if param_desc == '/':
                    for param in params[:i]:
                        param['kind'] = Parameter.POSITIONAL_ONLY
                    continue
                elif param_desc == '*':
                    kw_only = True
                    continue

                try:
                    param = params[i]
                except IndexError:
                    param = {
                        'names': set(),
                        'defaults': [],
                        'types': set(),
                        'kind': Parameter.POSITIONAL_OR_KEYWORD
                    }
                    params.append(param)

                    # if there's a form with fewer arguments, then this
                    # parameter must be optional
                    if line_nr > 0:
                        param['defaults'].append(Parameter.missing)

                if kw_only:
                    param['kind'] = Parameter.KEYWORD_ONLY

                name, _, default = param_desc.partition('=')

                # a name in square brackets means it's optional
                if name.startswith('['):
                    name = name[1:-1]
                    default = Parameter.missing
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

            annotation = common_ancestor(*param['types'])

            parameter = parameter_type(name, kind, default, annotation)
            parameters.append(parameter)

        return_annotation = common_ancestor(*return_types)

        return cls(parameters, return_annotation=return_annotation)
    
    @property
    def num_required_arguments(self):
        return sum(not p.is_optional for p in self)

    def __iter__(self):
        return iter(self.parameters.values())


def signature(func):
    return Signature.from_callable(func)

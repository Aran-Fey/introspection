
import re
import ast
import inspect
import functools

import datatypes

from .Parameter import Parameter

__all__ = ['get_configurable_attributes', 'get_constructor_parameters', 'get_parameters']


@functools.lru_cache()
def get_configurable_attributes(type):
    # FIXME: also look for settable properties
    attrs = get_constructor_parameters(type)
    return attrs


def get_constructor_parameters(type):
    return get_parameters(type)


@functools.lru_cache()
def get_parameters(callable):
    parameters = []

    try:
        sig = inspect.signature(callable)
    except ValueError:  # builtin types don't have an accessible signature
        # extract the parameter names and default values from the docstring
        doc = callable.__doc__
        pattern = re.compile(r'{}\((.*)\) -> '.format(callable.__name__))
        param_pattern = re.compile(r'(?P<name>\w+)(?:=(?P<default>[^,[)]+))?')

        for line in doc.splitlines():
            match = pattern.match(line)
            if not match:
                break

            paramlist = match.group(1)
            for i, match in enumerate(param_pattern.finditer(paramlist)):
                try:
                    param = parameters[i]
                except IndexError:
                    param = Parameter()
                    parameters.append(param)

                # many builtins accept a variable number of arguments, and
                # the different signatures are usually listed with an ascending
                # number of parameters.
                # Thanks to that, we can simply overwrite the parameter's attributes
                # and expect them to be correct in the end
                param.name = match.group('name')

                default = match.group('default')
                if default:
                    param.default_value = ast.literal_eval(default)

                    param.type = type(param.default_value)
    else:
        for parameter in sig.parameters.values():
            param_type = datatypes.Any() if parameter.annotation is inspect.Parameter.empty else parameter.annotation
            default_value = Parameter.NONE if parameter.default is inspect.Parameter.empty else parameter.default
            param = Parameter(parameter.name, param_type, default_value=default_value)
            parameters.append(param)

    return parameters
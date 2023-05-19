
import builtins
import collections
import importlib
import types
import typing
from typing import *

import typing_extensions

from .introspection import is_parameterized_generic, get_generic_base_class, get_type_arguments, get_type_name, _get_forward_ref_code
from .i_hate_circular_imports import parameterize
from ..parameter import Parameter
from ..signature import Signature
from ..types import Type_, ForwardRef, Annotation
from ..errors import *

__all__ = ['resolve_forward_refs', 'annotation_to_string', 'annotation_for_callable']


def resolve_forward_refs(
    annotation: Annotation,
    module: Optional[types.ModuleType] = None,
    eval_: bool = True,
    strict: bool = True,
) -> Annotation:
    """
    Resolves forward references in a type annotation.

    Examples::

        >>> resolve_forward_refs(List['int'])
        typing.List[int]
        >>> resolve_forward_refs('ellipsis')
        <class 'ellipsis'>

    :param annotation: The annotation in which forward references should be resolved
    :param module: The module in which forward references will be evaluated
    :param eval_: If ``True``, references may contain arbitrary code that will be evaluated with ``eval``. Otherwise, they must be identifiers and will be resolved with ``getattr``.
    :param strict: Whether to raise an exception if a forward reference can't be resolved
    :return: A new annotation with no forward references
    """
    if isinstance(module, str):
        module = importlib.import_module(module)

    if isinstance(annotation, ForwardRef):
        annotation = _get_forward_ref_code(annotation)

    if isinstance(annotation, str):
        if eval_:
            # Eval the code in a ChainMap so that names
            # can be resolved in the given module or in
            # the typing module
            modules: List[types.ModuleType] = [typing]
            if module is not None:
                modules.insert(0, module)

            scope = collections.ChainMap(*[vars(mod) for mod in modules])

            try:
                # the globals must be a real dict, so the scope will be
                # used as the locals
                annotation = eval(annotation, {}, scope)
            except Exception:
                pass
            else:
                return resolve_forward_refs(annotation, module, eval_, strict)
        else:
            # try to resolve the annotation in various
            # modules
            modules = [typing, builtins]
            if module is not None:
                modules.insert(0, module)

            attrs = annotation.split('.')

            for mod in modules:
                value = mod
                try:
                    for attr in attrs:
                        value = getattr(value, attr)

                    return value  # type: ignore
                except AttributeError:
                    pass

        if annotation == 'ellipsis':
            return type(...)

        if not strict:
            return annotation

        raise CannotResolveName(annotation, module)

    if isinstance(annotation, list):
        return [resolve_forward_refs(typ, module, eval_, strict) for typ in annotation]

    if not is_parameterized_generic(annotation, raising=False):
        return annotation

    base = get_generic_base_class(annotation)

    if base is typing_extensions.Literal:
        return annotation

    type_args = get_type_arguments(annotation)

    type_args = tuple(resolve_forward_refs(typ, module, eval_, strict) for typ in type_args)
    return parameterize(base, type_args)


def annotation_to_string(annotation: Type_, implicit_typing: bool = True) -> str:
    """
    Converts a type annotation to string. The result is
    valid python code.

    Examples::

        >>> annotation_to_string(int)
        'int'
        >>> annotation_to_string(None)
        'None'
        >>> annotation_to_string(typing.List[int])
        'List[int]'

    :param annotation: A class or type annotation
    :param implicit_typing: Whether to omit the "typing." prefix from ``typing`` types' names
    :return: A string that, when evaluated, returns ``annotation``
    """
    def process_nested(prefix, elems):
        elems = ', '.join(annotation_to_string(ann, implicit_typing) for ann in elems)
        return '{}[{}]'.format(prefix, elems)

    if isinstance(annotation, list):
        return process_nested('', annotation)

    if isinstance(annotation, ForwardRef):
        return repr(_get_forward_ref_code(annotation))

    if annotation is ...:
        return '...'

    if annotation is type(None):
        return 'None'

    if is_parameterized_generic(annotation, raising=False):
        base = get_generic_base_class(annotation)
        subtypes = get_type_arguments(annotation)

        prefix = annotation_to_string(base, implicit_typing)
        return process_nested(prefix, subtypes)

    if isinstance(annotation, (typing.TypeVar, typing_extensions.ParamSpec)):
        return str(annotation)

    if hasattr(annotation, '__module__'):
        if annotation.__module__ == 'builtins':
            return annotation.__qualname__
        elif annotation.__module__ in ('typing', 'typing_extensions'):
            annotation = get_type_name(annotation)

            if not implicit_typing:
                annotation = 'typing.' + annotation

            return annotation
        else:
            return '{}.{}'.format(annotation.__module__, annotation.__qualname__)

    return repr(annotation)


def annotation_for_callable(callable_: typing.Callable) -> Type_:
    """
    Given a callable object as input, returns a matching type annotation.

    Examples::

        >>> annotation_for_callable(len)
        typing.Callable[[typing.Sized], int]
    
    Note: How ``*args``, ``**kwargs``, and keyword-only parameters are handled
    is currently undefined.

    .. versionadded:: 1.5
    """
    signature = Signature.from_callable(callable_)
    parameters = signature.parameters.values()

    if signature.return_annotation is Signature.empty:
        return_type = typing.Any
    else:
        return_type = signature.return_annotation
    
    param_types = [
        typing.Any if param.annotation is Parameter.empty else param.annotation
        for param in parameters
        if param.kind <= Parameter.POSITIONAL_OR_KEYWORD
    ]  # TODO: Raise an exception if keyword-only parameters exist?

    # If some parameters are optional, we have to return a Union of Callable
    # types with fewer and fewer parameters
    options = [param_types]

    for param in reversed(parameters):
        if not param.is_optional:
            break

        param_types = param_types[:-1]
        options.append(param_types)

    if len(options) == 1:
        return typing.Callable[param_types, return_type]  # type: ignore
    
    options = tuple(
        typing.Callable[option, return_type]  # type: ignore
        for option in options
    )
    return typing.Union[options]  # type: ignore

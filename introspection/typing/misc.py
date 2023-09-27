import builtins
import collections
import importlib
import types
import typing
import warnings
from typing import *  # type: ignore

import typing_extensions

from .introspection import (
    is_parameterized_generic,
    get_generic_base_class,
    get_type_arguments,
    get_type_name,
    _get_forward_ref_code,
)
from .i_hate_circular_imports import parameterize
from ..parameter import Parameter
from ..signature import Signature
from ..types import Type_, TypeAnnotation
from ..errors import *

__all__ = ["resolve_forward_refs", "annotation_to_string", "annotation_for_callable"]


ForwardRefContext = typing.Union[None, type, types.FunctionType, types.ModuleType, str]


@overload
def resolve_forward_refs(
    annotation: TypeAnnotation,
    module: typing.Optional[types.ModuleType] = None,
    eval_: bool = True,
    strict: bool = True,
) -> TypeAnnotation:
    ...


@overload
def resolve_forward_refs(
    annotation: TypeAnnotation,
    context: ForwardRefContext = None,
    *,
    mode: Literal["eval", "getattr", "mixed"] = "mixed",
    strict: bool = True,
) -> TypeAnnotation:
    ...


def resolve_forward_refs(
    annotation: TypeAnnotation,
    module: typing.Optional[types.ModuleType] = None,
    eval_: bool = True,
    strict: bool = True,
    *,
    context: ForwardRefContext = None,
    mode: Literal["eval", "getattr", "mixed"] = "mixed",
) -> TypeAnnotation:
    """
    Resolves forward references in a type annotation.

    Examples::

        >>> resolve_forward_refs(List['int'])
        typing.List[int]
        >>> resolve_forward_refs('ellipsis')
        <class 'ellipsis'>

    .. versionchanged:: 1.6
        The ``module`` and ``eval_`` parameters are deprecated in favor of
        ``context`` and ``mode``. Once the ``eval_`` parameter is removed,
        the default ``mode`` will be changed to ``'mixed'``.

    :param annotation: The annotation in which forward references should be resolved
    :param context: The context in which forward references will be evaluated.
        Can be a class, a function, a module, or a string representing a module
        name. If ``None``, a namespace containing some common modules like
        ``typing`` and ``collections`` will be used.
    :param mode: If ``True``, references may contain arbitrary code that will
        be evaluated with ``eval``. Otherwise, they must be identifiers and will
        be resolved with ``getattr``.
    :param strict: Whether to raise an exception if a forward reference can't be resolved
    :return: A new annotation with no forward references
    """
    if module is not None:
        context = module
        warnings.warn(
            'The "module" parameter is deprecated in favor of "context"',
            DeprecationWarning,
        )

    if eval_ is not None:
        mode = "eval" if eval_ else "getattr"
        warnings.warn(
            'The "eval_" parameter is deprecated in favor of "mode"',
            DeprecationWarning,
        )

    if isinstance(context, str):
        context = importlib.import_module(context)

    if isinstance(annotation, ForwardRef):
        annotation = _get_forward_ref_code(annotation)

    if isinstance(annotation, str):
        if mode == "eval":
            # Eval the code in a ChainMap so that names
            # can be resolved in the given module or in
            # the typing module
            modules: List[types.ModuleType] = [typing]
            if isinstance(context, types.ModuleType):
                modules.insert(0, context)

            scope = collections.ChainMap(*[vars(mod) for mod in modules])

            try:
                # the globals must be a real dict, so the scope will be
                # used as the locals
                annotation = eval(annotation, {}, scope)
            except Exception:
                pass
            else:
                return resolve_forward_refs(annotation, context, eval_, strict)
        elif mode == "getattr":
            # try to resolve the annotation in various modules
            modules = [typing, builtins]
            if isinstance(context, types.ModuleType):
                modules.insert(0, context)

            attrs = annotation.split(".")

            for mod in modules:
                value = mod
                try:
                    for attr in attrs:
                        value = getattr(value, attr)

                    return value  # type: ignore
                except AttributeError:
                    pass
        else:
            raise NotImplementedError  # FIXME

        if annotation == "ellipsis":
            return type(...)

        if not strict:
            return annotation

        raise CannotResolveName(annotation, context)

    if isinstance(annotation, list):
        return [
            resolve_forward_refs(typ, context, mode=mode, strict=strict)
            for typ in annotation
        ]

    if not is_parameterized_generic(annotation, raising=False):
        return annotation

    base = get_generic_base_class(annotation)

    if base is typing_extensions.Literal:
        return annotation

    type_args = get_type_arguments(annotation)
    type_args = tuple(
        resolve_forward_refs(typ, context, mode=mode, strict=strict)
        for typ in type_args
    )
    return parameterize(base, type_args)


def annotation_to_string(
    annotation: TypeAnnotation,
    *,
    implicit_typing: bool = True,
    new_style_unions: bool = True,
    optional_as_union: bool = True,
) -> str:
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
    :param implicit_typing: Whether to omit the "typing." prefix from ``typing``
        types' names
    :param new_style_unions: Whether to use the new-style ``typing.Union`` syntax
        ``int | str`` instead of ``Union[int, str]``
    :return: A string that, when evaluated, returns ``annotation``
    """

    def recurse(annotation):
        return annotation_to_string(
            annotation,
            implicit_typing=implicit_typing,
            new_style_unions=new_style_unions,
            optional_as_union=optional_as_union,
        )

    def process_nested(prefix, elems):
        elems = ", ".join(recurse(ann) for ann in elems)
        return "{}[{}]".format(prefix, elems)

    if isinstance(annotation, list):
        return process_nested("", annotation)

    if isinstance(annotation, ForwardRef):
        return repr(_get_forward_ref_code(annotation))

    if annotation is ...:
        return "..."

    if annotation is type(None):
        return "None"

    if is_parameterized_generic(annotation, raising=False):
        base = get_generic_base_class(annotation)
        subtypes = get_type_arguments(annotation)

        if base is typing.Optional and optional_as_union:
            base = typing.Union
            subtypes = [subtypes[0], None]

        if base is typing.Union and new_style_unions:
            return " | ".join(recurse(sub) for sub in subtypes)

        prefix = recurse(base)
        return process_nested(prefix, subtypes)

    if isinstance(annotation, (typing.TypeVar, typing_extensions.ParamSpec)):
        return str(annotation)

    if hasattr(annotation, "__module__"):
        if annotation.__module__ == "builtins":
            return annotation.__qualname__
        elif annotation.__module__ in ("typing", "typing_extensions"):
            annotation = get_type_name(annotation)

            if not implicit_typing:
                annotation = "typing." + annotation

            return annotation
        else:
            return "{}.{}".format(annotation.__module__, annotation.__qualname__)

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
        typing.Callable[option, return_type] for option in options  # type: ignore
    )
    return typing.Union[options]  # type: ignore

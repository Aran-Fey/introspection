from __future__ import annotations

import ast
import builtins
import collections.abc
import importlib
import types
import typing
import warnings
from typing import *

import typing_extensions

from ._compat import LITERAL_TYPES
from .introspection import (
    is_parameterized_generic,
    get_generic_base_class,
    get_type_arguments,
    get_type_name,
    _get_forward_ref_code,
)
from .i_hate_circular_imports import parameterize
from ..parameter import Parameter
from ..signature_ import Signature
from ..types import Type_, TypeAnnotation, ForwardReference, ForwardRefContext
from ..errors import *

__all__ = [
    "is_forward_ref",
    "resolve_forward_refs",
    "annotation_to_string",
    "annotation_for_callable",
]


def is_forward_ref(
    annotation: TypeAnnotation,
) -> typing_extensions.TypeGuard[ForwardReference]:
    """ """
    return isinstance(annotation, (str, ForwardRef))


@overload
def resolve_forward_refs(
    annotation: TypeAnnotation,
    context: ForwardRefContext = None,
    *,
    mode: Literal["eval", "getattr", "ast"] = "eval",
    strict: bool = True,
    max_depth: Optional[int] = None,
    extra_globals: Mapping[str, object] = {},
    treat_name_errors_as_imports: bool = False,
) -> TypeAnnotation: ...


@overload
def resolve_forward_refs(
    annotation: TypeAnnotation,
    module: typing.Optional[types.ModuleType] = None,
    eval_: bool = True,
    strict: bool = True,
) -> TypeAnnotation: ...


def resolve_forward_refs(  # type: ignore
    annotation: TypeAnnotation,
    context: ForwardRefContext = None,
    eval_: Optional[bool] = None,
    strict: bool = True,
    *,
    module: typing.Optional[types.ModuleType] = None,
    mode: Literal["eval", "getattr", "ast"] = "eval",
    max_depth: Optional[int] = None,
    extra_globals: Mapping[str, object] = {},
    treat_name_errors_as_imports: bool = False,
    _currently_evaluating: AbstractSet[Tuple[str, int]] = set(),
) -> TypeAnnotation:
    """
    Resolves forward references in a type annotation.

    Examples::

        >>> resolve_forward_refs(List['int'])
        typing.List[int]
        >>> resolve_forward_refs('ellipsis')
        <class 'ellipsis'>

    Using `mode='ast'` makes partial evaluation possible::

        >>> resolve_forward_refs('List[ThisCantBeResolved'], mode='ast', strict=False)
        List['ThisCantBeResolved']

    .. versionchanged:: 1.6
        The ``module`` and ``eval_`` parameters are deprecated in favor of
        ``context`` and ``mode``.

    :param annotation: The annotation in which forward references should be resolved
    :param context: The context in which forward references will be evaluated.
        Can be a class, a function, a module, or a string representing a module
        name. If ``None``, a namespace containing some common modules like
        ``typing`` and ``collections`` will be used.
    :param mode: If ``'eval'``, references may contain arbitrary code that will
        be evaluated with ``eval``. If ``'getattr'``, they must be identifiers
        and will be resolved with ``getattr``.
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
        mode = "eval" if eval_ else "ast"
        warnings.warn(
            'The "eval_" parameter is deprecated in favor of "mode"',
            DeprecationWarning,
        )

    if max_depth is None:
        max_depth = cast(int, float("inf"))
    elif max_depth <= 0:
        return annotation

    def recurse(annotation: TypeAnnotation) -> TypeAnnotation:
        return resolve_forward_refs(
            annotation,
            context,
            mode=mode,
            strict=strict,
            max_depth=max_depth - 1,
            extra_globals=extra_globals,
            _currently_evaluating=_currently_evaluating,  # type: ignore
        )

    if isinstance(annotation, ForwardRef):
        if context is None:
            context = annotation.__forward_module__

        annotation = _get_forward_ref_code(annotation)

    if isinstance(annotation, str):
        # First, check if this exact same forward reference is already being evaluated - i.e. it is
        # a recursive type.
        key = (annotation, id(context))
        if key in _currently_evaluating:
            return annotation
        _currently_evaluating = _currently_evaluating | {key}

        scope: collections.ChainMap[str, object] = collections.ChainMap()

        if context is None:
            scope.maps.extend(
                vars(module)
                for module in (collections.abc, collections, typing, typing_extensions)  # type: ignore
            )
        elif isinstance(context, types.ModuleType):
            scope.maps.append(vars(context))
        elif isinstance(context, str):
            module = importlib.import_module(context)
            scope.maps.append(vars(module))
        elif isinstance(context, collections.abc.Mapping):
            scope.maps.append(context)  # type: ignore
        else:
            module = importlib.import_module(context.__module__)
            scope.maps.append(vars(module))

        scope.maps.append(vars(builtins))  # type: ignore
        scope.maps.append(extra_globals)  # type: ignore

        if treat_name_errors_as_imports:
            from ._utils import ImporterDict

            scope.maps.append(ImporterDict())  # type: ignore

        # Note: Annotations can be strings inside of strings, like `"'int'"`. So evaluating it once
        # isn't necessarily enough; make sure to call `recurse()` with the result!
        if mode == "eval":
            try:
                # The globals must be a real dict, so the scope will be used as
                # the locals
                annotation = eval(annotation, {}, scope)
            except Exception:
                pass
            else:
                return recurse(annotation)
        elif mode == "getattr":
            first_name, *attrs = annotation.split(".")

            try:
                value = scope[first_name]
            except KeyError:
                pass
            else:
                try:
                    for attr in attrs:
                        value = getattr(value, attr)

                    return recurse(value)  # type: ignore
                except AttributeError:
                    pass
        elif mode == "ast":
            expr = ast.parse(annotation, mode="eval")
            try:
                result = _eval_ast(
                    expr.body,
                    scope,
                    strict=strict,
                    max_depth=max_depth,
                    treat_name_errors_as_imports=treat_name_errors_as_imports,
                )
            except Exception:
                pass
            else:
                return recurse(result)  # type: ignore
        else:
            assert False, f"Invalid mode: {mode!r}"

        if annotation == "ellipsis":
            return type(...)

        if not strict:
            return annotation

        raise CannotResolveForwardref(annotation, context)

    if annotation is None:
        return None

    # In some versions, `ParamSpec` is a subclass of `list`, so make sure this
    # check happens before the `isinstance(annotation, list)` check below
    if type(annotation) in (
        typing_extensions.TypeVarTuple,
        typing_extensions.ParamSpec,
        typing_extensions.ParamSpecKwargs,
        typing_extensions.ParamSpecArgs,
    ):
        return annotation

    if isinstance(annotation, TypeVar):
        if annotation.__constraints__:
            constraints = [recurse(constraint) for constraint in annotation.__constraints__]
            bound = None
        else:
            constraints = ()
            bound = recurse(annotation.__bound__)

        return TypeVar(
            annotation.__name__,  # type: ignore
            *constraints,  # type: ignore
            bound=bound,  # type: ignore
            covariant=annotation.__covariant__,  # type: ignore
            contravariant=annotation.__contravariant__,  # type: ignore
        )

    if not is_parameterized_generic(annotation, raising=False):
        return annotation

    base = get_generic_base_class(annotation)

    # Handle special cases where we can't blindly recurse into the subtypes
    if base in LITERAL_TYPES:
        return annotation

    if base is typing_extensions.Annotated:
        type_args = list(get_type_arguments(annotation))
        type_args[0] = recurse(type_args[0])  # type: ignore
        return parameterize(base, type_args)

    if base in (typing.Callable, collections.abc.Callable):
        arg_types, return_type = get_type_arguments(annotation)

        if isinstance(arg_types, list):
            arg_types = [recurse(typ) for typ in arg_types]

        return_type = recurse(return_type)  # type: ignore

        return parameterize(base, (arg_types, return_type))

    type_args = get_type_arguments(annotation)
    type_args = tuple(recurse(typ) for typ in type_args)  # type: ignore
    return parameterize(base, type_args)


def _eval_ast(
    node: ast.AST,
    scope: typing.Mapping[str, object],
    strict: bool,
    max_depth: int,
    treat_name_errors_as_imports: bool,
) -> object:
    # Compared to "eval" and "getattr", this method of evaluating forward refs
    # has the advantage of being able to perform partial evaluation. For
    # example, the forward ref `"ClassVar[NameThatCannotBeResolved]"` can be
    # turned into `ClassVar["NameThatCannotBeResolved"]`.

    def recurse(node: ast.AST) -> object:
        if max_depth <= 1:
            return ast.unparse(node)

        return _eval_ast(node, scope, strict, max_depth - 1, treat_name_errors_as_imports)

    if strict:
        safe_recurse = recurse
    else:

        def safe_recurse(node: ast.AST) -> object:
            try:
                return recurse(node)
            except Exception:
                return ast.unparse(node)

    def safe_recurse_if_forwardref(obj: object) -> object:
        if max_depth <= 1:
            return obj

        return resolve_forward_refs(
            obj,  # type: ignore
            scope,
            mode="ast",
            strict=strict,
            max_depth=max_depth - 1,
            treat_name_errors_as_imports=treat_name_errors_as_imports,
        )

    if type(node) is ast.Name:
        name = node.id
        return scope[name]
    elif type(node) is ast.Attribute:
        obj = recurse(node.value)

        try:
            return getattr(obj, node.attr)
        except AttributeError:
            # The parameter name is a little misleading, but we'll also treat AttributeErrors on
            # modules as missing imports
            if not treat_name_errors_as_imports or not isinstance(obj, types.ModuleType):
                raise

            try:
                importlib.import_module(f"{obj.__name__}.{node.attr}")
            except ImportError:
                pass

            try:
                return getattr(obj, node.attr)
            except AttributeError:
                pass

            raise
    elif type(node) is ast.Subscript:
        generic_type = recurse(node.value)
        subtype = safe_recurse(node.slice)

        # If we're dealing with `typing.Literal` or `typing.Annotated`, we must leave strings as
        # strings. But for any other type, we must treat them as forward references.
        if generic_type in LITERAL_TYPES:
            pass
        elif generic_type is typing_extensions.Annotated:
            assert isinstance(subtype, tuple)
            typ, *annotations = subtype
            subtype = (safe_recurse(typ), *annotations)
        else:
            if isinstance(subtype, tuple):
                subtype = tuple(safe_recurse_if_forwardref(t) for t in subtype)
            else:
                subtype = safe_recurse_if_forwardref(subtype)

        return generic_type[subtype]  # type: ignore
    elif type(node) is ast.Constant:
        return node.value
    elif type(node) is ast.Tuple:
        return tuple(safe_recurse(elt) for elt in node.elts)
    elif type(node) is ast.List:
        return [safe_recurse(elt) for elt in node.elts]
    elif type(node) is ast.BinOp:
        if type(node.op) is ast.BitOr:
            left = safe_recurse(node.left)
            right = safe_recurse(node.right)
            # Use `Union` instead of `|` because:
            # 1. It works in older python versions
            # 2. It works even if `left` and `right` are strings because they
            #    couldn't be resolved
            return Union[left, right]  # type: ignore

    raise NotImplementedError(f"Can't evaluate AST node {node}")


def annotation_to_string(
    annotation: TypeAnnotation,
    *,
    implicit_typing: bool = True,
    new_style_unions: bool = True,
    optional_as_union: bool = True,
    variance_prefixes: bool = False,
) -> str:
    """
    Converts a type annotation to string. The result is valid python code
    (unless ``variance_prefixes`` is set to ``True``).

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
    :param variance_prefixes: Whether `TypeVars` and `ParamSpecs` should be
        prefixed with ``+``, ``-``, or ``~`` to indicate variance
    :return: A string that, when evaluated, returns ``annotation``
    """

    def recurse(annotation: TypeAnnotation) -> str:
        return annotation_to_string(
            annotation,
            implicit_typing=implicit_typing,
            new_style_unions=new_style_unions,
            optional_as_union=optional_as_union,
            variance_prefixes=variance_prefixes,
        )

    def process_nested(prefix: str, elems: Iterable[TypeAnnotation]):
        elems = ", ".join(recurse(ann) for ann in elems)
        return "{}[{}]".format(prefix, elems)

    if isinstance(annotation, ForwardRef):
        return _get_forward_ref_code(annotation)

    if isinstance(annotation, str):
        return annotation

    if annotation is ...:
        return "..."

    if annotation in (None, type(None)):
        return "None"

    if is_parameterized_generic(annotation, raising=False):
        base = get_generic_base_class(annotation)
        subtypes = get_type_arguments(annotation)

        if base is typing.Optional and optional_as_union:
            base = typing.Union
            subtypes = [subtypes[0], None]

        if base is typing.Union and new_style_unions:
            return " | ".join(recurse(sub) for sub in subtypes)  # type: ignore

        if base in (typing.Callable, collections.abc.Callable):
            param_types, return_type = subtypes

            prefix = recurse(base)
            return_str = recurse(return_type)  # type: ignore

            if isinstance(param_types, list):
                params = ", ".join(recurse(param_type) for param_type in param_types)
                params = f"[{params}]"
            else:
                params = "..."

            return f"{prefix}[{params}, {return_str}]"

        if base in LITERAL_TYPES:
            literals = ", ".join(repr(value) for value in subtypes)
            prefix = recurse(base)
            return f"{prefix}[{literals}]"

        if base is typing_extensions.Annotated:
            sub_type, *annotations = subtypes
            sub_strs = [recurse(sub_type)]  # type: ignore
            sub_strs.extend(repr(ann) for ann in annotations)

            prefix = recurse(base)
            return f'{prefix}[{", ".join(sub_strs)}]'

        prefix = recurse(base)
        return process_nested(prefix, subtypes)  # type: ignore

    if isinstance(annotation, (typing.TypeVar, typing_extensions.ParamSpec)):
        result = annotation.__name__

        if variance_prefixes:
            if annotation.__covariant__:
                result = "+" + result
            elif annotation.__contravariant__:
                result = "-" + result
            else:
                result = "~" + result

        return result

    if isinstance(annotation, typing_extensions.TypeVarTuple):
        return annotation.__name__

    if isinstance(annotation, typing_extensions.ParamSpecArgs):
        return recurse(annotation.__origin__) + ".args"

    if isinstance(annotation, typing_extensions.ParamSpecKwargs):
        return recurse(annotation.__origin__) + ".kwargs"

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

    return repr(annotation)  # This point should never be reached, but just in case...


def annotation_for_callable(callable_: typing.Callable[..., object]) -> Type_:
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

    options = tuple(typing.Callable[option, return_type] for option in options)  # type: ignore
    return typing.Union[options]  # type: ignore

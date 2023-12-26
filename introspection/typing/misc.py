import ast
import builtins
import collections.abc
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
from ..signature_ import Signature
from ..types import Type_, TypeAnnotation, ForwardRefContext
from ..errors import *

__all__ = ["resolve_forward_refs", "annotation_to_string", "annotation_for_callable"]


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
    mode: Literal["eval", "getattr", "ast"] = "eval",
    strict: bool = True,
    extra_globals: typing.Mapping[str, object] = {},
) -> TypeAnnotation:
    ...


def resolve_forward_refs(
    annotation: TypeAnnotation,
    context: ForwardRefContext = None,
    eval_: Optional[bool] = None,
    strict: bool = True,
    *,
    module: typing.Optional[types.ModuleType] = None,
    mode: Literal["eval", "getattr", "ast"] = "eval",
    extra_globals: typing.Mapping[str, object] = {},
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

    if isinstance(context, str):
        context = importlib.import_module(context)

    if isinstance(annotation, ForwardRef):
        if context is None:
            context = annotation.__forward_module__

        annotation = _get_forward_ref_code(annotation)

    if isinstance(annotation, str):
        scope = collections.ChainMap()
        scope.maps.append(extra_globals)  # type: ignore

        if context is None:
            scope.maps.extend(vars(module) for module in (builtins, typing, collections.abc, collections))  # type: ignore
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

        if mode == "eval":
            try:
                # The globals must be a real dict, so the scope will be used as
                # the locals
                annotation = eval(annotation, {}, scope)
            except Exception:
                pass
            else:
                return resolve_forward_refs(
                    annotation, context, mode=mode, strict=strict
                )
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

                    return value  # type: ignore
                except AttributeError:
                    pass
        elif mode == "ast":
            try:
                expr = ast.parse(annotation, mode="eval")
                _, result = _eval_ast(expr.body, scope, strict=strict)
                return result  # type: ignore
            except SyntaxError:
                pass
        else:
            assert False, "Invalid mode: {!r}".format(mode)

        if annotation == "ellipsis":
            return type(...)

        if not strict:
            return annotation

        raise CannotResolveForwardref(annotation, context)

    # In some versions, `ParamSpec` is a subclass of `list`, so make sure this
    # check happens before the `isinstance(annotation, list)` check below
    if type(annotation) in (
        typing.TypeVar,
        typing_extensions.TypeVarTuple,
        typing_extensions.ParamSpec,
        typing_extensions.ParamSpecKwargs,
        typing_extensions.ParamSpecArgs,
    ):
        return annotation

    # As a special case, lists are also supported because they're used by
    # `Callable`
    if isinstance(annotation, list):
        return [
            resolve_forward_refs(typ, context, mode=mode, strict=strict)
            for typ in annotation
        ]  # type: ignore

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


def _eval_ast(
    node: ast.AST, scope: typing.Mapping[str, object], strict: bool
) -> Tuple[bool, object]:
    # Compared to "eval" and "getattr", this method of evaluating forward refs
    # has the advantage of being able to perform partial evaluation. For
    # example, the forward ref `"ClassVar[NameThatCannotBeResolved]"` can be
    # turned into `ClassVar["NameThatCannotBeResolved"]`.
    #
    # Sometimes we need to know whether the forward ref was resolved or not.
    # That's why this function returns a tuple of `(bool, object)`.
    def recurse(node: ast.AST) -> Tuple[bool, object]:
        return _eval_ast(node, scope, strict)

    if type(node) is ast.Name:
        name = node.id
        try:
            return True, scope[name]
        except KeyError:
            if strict:
                raise NameError(name) from None
            else:
                return False, name
    elif type(node) is ast.Attribute:
        success, obj = recurse(node.value)
        if not success:
            raise SyntaxError(f"Failed to resolve {ast.dump(node.value)}")

        try:
            return True, getattr(obj, node.attr)
        except AttributeError as error:
            if (
                not strict
                and isinstance(obj, types.ModuleType)
                and str(error).startswith("partially initialized module")
            ):
                return False, ast.dump(node)
            raise
    elif type(node) is ast.Subscript:
        success, generic_type = recurse(node.value)
        if not success:
            if strict:
                raise SyntaxError(f"Failed to resolve {ast.dump(node.value)}")
            else:
                return False, ast.dump(node)

        _, subtype = recurse(node.slice)
        return True, generic_type[subtype]  # type: ignore
    elif type(node) is ast.Constant:
        return True, node.value
    elif type(node) is ast.Tuple:
        return True, tuple(recurse(elt)[1] for elt in node.elts)
    elif type(node) is ast.List:
        return True, [recurse(elt)[1] for elt in node.elts]
    elif type(node) is ast.BinOp:
        if type(node.op) is ast.BitOr:
            _, left = recurse(node.left)
            _, right = recurse(node.right)
            # Use `Union` instead of `|` because:
            # 1. It works in older python versions
            # 2. It works even if `left` and `right` are strings because they
            #    couldn't be resolved
            return True, Union[left, right]  # type: ignore

    raise SyntaxError(f"Unsupported AST node: {node!r}")


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

    return repr(annotation)


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

    options = tuple(
        typing.Callable[option, return_type] for option in options  # type: ignore
    )
    return typing.Union[options]  # type: ignore

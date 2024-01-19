import collections
import functools
import inspect
from typing import *
from typing_extensions import Self, Concatenate

from .argument_bundle import ArgumentBundle
from .misc import rename
from .parameter import Parameter
from .signature_ import Signature
from .types import P, T, Type_, NONE


__all__ = [
    "signature",
    "get_parameters",
    "set_signature",
    "replace_varargs",
    "wraps",
    "split_arguments",
]


# Unchanged signature
@overload
def set_signature(
    signature: Union[Callable[P, T], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: Literal[False] = False,
) -> Callable[[Callable[..., object]], Callable[P, T]]:
    ...


# Self parameter added
@overload
def set_signature(
    signature: Union[Callable[P, T], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: Literal[True],
) -> Callable[[Callable[..., object]], Callable[Concatenate[Any, P], T]]:
    ...


# Return annotation changed
@overload
def set_signature(
    signature: Union[Callable[P, object], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: Literal[False] = False,
    return_annotation: Type[T],
) -> Callable[[Callable[..., object]], Callable[P, T]]:
    ...


# Self parameter added and return annotation changed
@overload
def set_signature(
    signature: Union[Callable[P, object], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: Literal[True],
    return_annotation: Type[T],
) -> Callable[[Callable[..., object]], Callable[Concatenate[Any, P], T]]:
    ...


# Parameters removed
@overload
def set_signature(
    signature: Union[Callable[..., T], inspect.Signature],
    *,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
    add_self: Literal[False] = False,
) -> Callable[[Callable[..., object]], Callable[..., T]]:
    ...


# Parameters removed and Self added
@overload
def set_signature(
    signature: Union[Callable[..., T], inspect.Signature],
    *,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
    add_self: Literal[True],
    # The return type should ideally be Callable[Concatenate[Self, ...], T], but
    # that crashes in 3.10
) -> Callable[[Callable[..., object]], Callable[..., T]]:
    ...


# Parameters removed and return annotation changed
@overload
def set_signature(
    signature: Union[Callable[..., object], inspect.Signature],
    *,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
    add_self: Literal[False] = False,
    return_annotation: Type[T],
) -> Callable[[Callable[..., object]], Callable[..., T]]:
    ...


# Parameters removed, return annotation changed and Self added
@overload
def set_signature(
    signature: Union[Callable[..., object], inspect.Signature],
    *,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
    add_self: Literal[True],
    return_annotation: Type[T],
    # The return type should ideally be Callable[Concatenate[Self, ...], T], but
    # that crashes in 3.10
) -> Callable[[Callable[..., object]], Callable[..., T]]:
    ...


def set_signature(  # type: ignore[wtf]
    signature: Union[Callable[P, T], inspect.Signature],
    *,
    remove_parameters: Optional[Iterable[Union[str, int, inspect._ParameterKind]]] = None,
    return_annotation: Type_ = NONE,  # type: ignore
    add_self: bool = False,
) -> Callable[[Callable[..., object]], Callable[P, T]]:
    if not isinstance(signature, inspect.Signature):
        signature = Signature.from_callable(signature)
    elif not isinstance(signature, Signature):
        signature = Signature.from_signature(signature)

    if remove_parameters:
        signature = signature.without_parameters(*remove_parameters)

    if add_self:
        # TODO: Find an unused name
        signature = signature.with_new_parameter(
            0, Parameter("self", Parameter.POSITIONAL_ONLY, annotation=Self)
        )

    if return_annotation is not NONE:
        signature = signature.replace(return_annotation=return_annotation)

    def decorator(func: Callable) -> Callable[P, T]:
        func.__signature__ = signature
        return func  # type: ignore

    return decorator


@set_signature(Signature.from_callable)
def signature(*args, **kwargs) -> Signature:
    """
    Shorthand for :meth:`Signature.from_callable`.
    """
    return Signature.from_callable(*args, **kwargs)


def get_parameters(callable_: Callable[..., object]) -> List[Parameter]:
    """
    Returns a list of parameters accepted by ``callable_``.

    :param callable_: The callable whose parameters to retrieve
    :return: A list of :class:`Parameter` instances
    """
    return list(Signature.from_callable(callable_).parameters.values())


def replace_varargs(
    signature: Union[Callable[..., T], inspect.Signature],
    remove_parameters: Optional[Iterable[Union[str, int, inspect._ParameterKind]]] = None,
) -> Callable[[Callable[..., object]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        merged_signature = Signature.from_callable(func).replace_varargs(signature)

        if remove_parameters:
            merged_signature = merged_signature.without_parameters(*remove_parameters)

        func.__signature__ = merged_signature
        return func

    return decorator  # type: ignore


# Case 1: No parameters removed, return annotation unchanged
@overload
def wraps(
    wrapped_func: Callable[P, T],
    *,
    name: Optional[str] = None,
    signature: Union[None, inspect.Signature, Callable] = None,
    remove_parameters: None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


# Case 2: No parameters removed, return annotation changed
@overload
def wraps(
    wrapped_func: Callable[P, Any],
    *,
    name: Optional[str] = None,
    signature: Union[None, inspect.Signature, Callable[..., object]] = None,
    remove_parameters: None = None,
    return_annotation: Type[T],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


# Case 3: Parameters removed, return annotation unchanged
@overload
def wraps(
    wrapped_func: Callable[..., T],
    *,
    name: Optional[str] = None,
    signature: Union[None, inspect.Signature, Callable[..., object]] = None,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


# Case 4: Parameters removed, return annotation changed
@overload
def wraps(
    wrapped_func: Callable[..., Any],
    *,
    name: Optional[str] = None,
    signature: Union[None, inspect.Signature, Callable[..., object]] = None,
    remove_parameters: Iterable[Union[str, int, inspect._ParameterKind]],
    return_annotation: Type[T],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


def wraps(  # type: ignore
    wrapped_func: Callable,
    *,
    name: Optional[str] = None,
    signature: Union[None, inspect.Signature, Callable[..., object]] = None,
    remove_parameters: Optional[Iterable[Union[str, int, inspect._ParameterKind]]] = None,
    return_annotation: Type_ = NONE,  # type: ignore
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Similar to :func:`functools.wraps`, but allows you to modify the function's
    metadata.

    .. versionadded:: 1.4

    :param wrapped_func: The wrapped function
    :param name: A new name for the wrapper function
    :param signature: A new signature for the wrapper function
    :param remove_parameters: Parameter names or indices to remove from the
        wrapper function's signature
    """

    def wrapper(wrapper_func: Callable[P, T]) -> Callable[P, T]:
        functools.update_wrapper(wrapper_func, wrapped_func)

        if name is not None:
            rename(wrapper_func, name)

        if signature is not None or remove_parameters is not None or return_annotation is not NONE:
            if signature is None:
                sig = Signature.from_callable(wrapped_func)
            elif isinstance(signature, inspect.Signature):
                sig = Signature.from_signature(signature)
            else:
                sig = Signature.from_callable(signature)

            if remove_parameters:
                sig = sig.without_parameters(*remove_parameters)

            if return_annotation is not NONE:
                sig = sig.replace(return_annotation=return_annotation)

            wrapper_func.__signature__ = sig

        return wrapper_func

    return wrapper


def split_arguments(
    signature: Union[Callable[P, Any], Signature, inspect.Signature],
    *args: object,
    **kwargs: object,
) -> Tuple[ArgumentBundle[P], ArgumentBundle]:
    """
    Given a signature (or callable) and arguments, splits the arguments into
    two pairs: Those that match the given signature, and those that don't.

    This is useful in situations where you would need multiple ``*args, **kwargs``
    for different purposes, for example::

        class Child(Parent1, Parent2):
            def __init__(self, *args, **kwargs):
                parent1_args, parent2_args = split_arguments(Parent1, *args, **kwargs)

                Parent1.__init__(self, *parent1_args.args, **parent1_args.kwargs)
                Parent2.__init__(self, *parent2_args.args, **parent2_args.kwargs)
    """
    if not isinstance(signature, inspect.Signature):
        signature = Signature.from_callable(signature)

    func_args = []
    func_kwargs = {}

    params = collections.deque(signature.parameters.values())

    # Positional arguments
    args_q = collections.deque(args)
    while params:
        if not args_q:
            break

        param = params[0]
        if param.kind > inspect.Parameter.POSITIONAL_OR_KEYWORD:
            break

        func_args.append(args_q.popleft())

        if param.kind != inspect.Parameter.VAR_POSITIONAL:
            del params[0]

    # Keyword arguments
    for param in params:
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.VAR_POSITIONAL,
        ):
            continue

        if param.kind == inspect.Parameter.VAR_KEYWORD:
            func_kwargs.update(kwargs)
            kwargs.clear()
            break

        try:
            value = kwargs.pop(param.name)
        except KeyError:
            continue

        func_kwargs[param.name] = value

    bundle1 = ArgumentBundle(*func_args, **func_kwargs)  # type: ignore
    bundle2 = ArgumentBundle(*args_q, **kwargs)  # type: ignore
    return bundle1, bundle2

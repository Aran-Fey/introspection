import collections
import functools
import inspect
import typing_extensions as t

from .argument_bundle import ArgumentBundle
from .misc import rename
from .parameter import Parameter
from .signature_ import Signature
from .types import P, T, Type_, NONE


__all__ = [
    "signature",
    "get_parameters",
    "set_signature",
    "set_parameters",
    "set_return_annotation",
    "replace_varargs",
    "wraps",
    "split_arguments",
]


# Unchanged signature
@t.overload
def set_signature(
    signature: t.Union[t.Callable[P, T], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: t.Literal[False] = False,
) -> t.Callable[[t.Callable[..., object]], t.Callable[P, T]]: ...


# Self parameter added
@t.overload
def set_signature(
    signature: t.Union[t.Callable[P, T], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: t.Literal[True],
) -> t.Callable[[t.Callable[..., object]], t.Callable[t.Concatenate[t.Any, P], T]]: ...


# Return annotation changed
@t.overload
def set_signature(
    signature: t.Union[t.Callable[P, object], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: t.Literal[False] = False,
    return_annotation: t.Type[T],
) -> t.Callable[[t.Callable[..., object]], t.Callable[P, T]]: ...


# Self parameter added and return annotation changed
@t.overload
def set_signature(
    signature: t.Union[t.Callable[P, object], inspect.Signature],
    *,
    remove_parameters: None = None,
    add_self: t.Literal[True],
    return_annotation: t.Type[T],
) -> t.Callable[[t.Callable[..., object]], t.Callable[t.Concatenate[t.Any, P], T]]: ...


# Parameters removed
@t.overload
def set_signature(
    signature: t.Union[t.Callable[..., T], inspect.Signature],
    *,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
    add_self: t.Literal[False] = False,
) -> t.Callable[[t.Callable[..., object]], t.Callable[..., T]]: ...


# Parameters removed and Self added
@t.overload
def set_signature(
    signature: t.Union[t.Callable[..., T], inspect.Signature],
    *,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
    add_self: t.Literal[True],
    # The return t.type should ideally be t.Callable[t.Concatenate[Self, ...], T], but
    # that crashes in 3.10
) -> t.Callable[[t.Callable[..., object]], t.Callable[..., T]]: ...


# Parameters removed and return annotation changed
@t.overload
def set_signature(
    signature: t.Union[t.Callable[..., object], inspect.Signature],
    *,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
    add_self: t.Literal[False] = False,
    return_annotation: t.Type[T],
) -> t.Callable[[t.Callable[..., object]], t.Callable[..., T]]: ...


# Parameters removed, return annotation changed and Self added
@t.overload
def set_signature(
    signature: t.Union[t.Callable[..., object], inspect.Signature],
    *,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
    add_self: t.Literal[True],
    return_annotation: t.Type[T],
    # The return t.type should ideally be t.Callable[t.Concatenate[Self, ...], T], but
    # that crashes in 3.10
) -> t.Callable[[t.Callable[..., object]], t.Callable[..., T]]: ...


def set_signature(  # type: ignore[wtf]
    signature: t.Union[t.Callable[P, T], inspect.Signature],
    *,
    remove_parameters: t.Optional[t.Iterable[t.Union[str, int, inspect._ParameterKind]]] = None,
    return_annotation: Type_ = NONE,  # type: ignore
    add_self: bool = False,
) -> t.Callable[[t.Callable[..., object]], t.Callable[P, T]]:
    """
    This is a function decorator that overwrites the decorated function's signature.

    Example::

        @set_signature(round)
        def round_and_increment(*args, **kwargs):
            return round(*args, **kwargs) + 1

        print(introspection.signature(round_and_increment))
        # Output: <Signature (number: numbers.Number[, ndigits: int], /) -> numbers.Number>
    """

    if not isinstance(signature, inspect.Signature):
        signature = Signature.from_callable(signature)
    elif not isinstance(signature, Signature):
        signature = Signature.from_signature(signature)

    if remove_parameters:
        signature = signature.without_parameters(*remove_parameters)

    if add_self:
        # TODO: Find an unused name
        signature = signature.with_new_parameter(
            0, Parameter("self", Parameter.POSITIONAL_ONLY, annotation=t.Self)
        )

    if return_annotation is not NONE:
        signature = signature.replace(return_annotation=return_annotation)

    def decorator(func: t.Callable) -> t.Callable[P, T]:
        func.__signature__ = signature  # type: ignore
        return func  # type: ignore

    return decorator


def set_parameters(
    signature: t.Union[t.Callable[P, t.Any], inspect.Signature],
) -> t.Callable[[t.Callable[..., T]], t.Callable[P, T]]:
    """
    This is a function decorator similar to :func:`set_signature`, except that it only changes the
    parameters and not the return type.

    .. versionadded:: 1.11.1
    """
    if not isinstance(signature, inspect.Signature):
        signature = Signature.from_callable(signature)
    elif not isinstance(signature, Signature):
        signature = Signature.from_signature(signature)

    def decorator(func: t.Callable) -> t.Callable[P, T]:
        func_signature = Signature.from_callable(func)

        combined_signature = signature.replace(return_annotation=func_signature.return_annotation)

        func.__signature__ = combined_signature  # type: ignore
        return func  # type: ignore

    return decorator


def set_return_annotation(
    signature: t.Union[t.Callable[P, t.Any], inspect.Signature],
) -> t.Callable[[t.Callable[..., T]], t.Callable[P, T]]:
    """
    This is a function decorator similar to :func:`set_signature`, except that it only changes the
    return type and not the parameters.

    .. versionadded:: 1.11.1
    """
    if not isinstance(signature, inspect.Signature):
        signature = Signature.from_callable(signature)
    elif not isinstance(signature, Signature):
        signature = Signature.from_signature(signature)

    def decorator(func: t.Callable) -> t.Callable[P, T]:
        func_signature = Signature.from_callable(func)

        combined_signature = func_signature.replace(return_annotation=signature.return_annotation)

        func.__signature__ = combined_signature  # type: ignore
        return func  # type: ignore

    return decorator


@set_signature(Signature.from_callable)
def signature(*args, **kwargs) -> Signature:
    """
    Shorthand for :meth:`Signature.from_callable`.
    """
    return Signature.from_callable(*args, **kwargs)


def get_parameters(callable_: t.Callable[..., object]) -> t.List[Parameter]:
    """
    Returns a list of parameters accepted by ``callable_``.

    :param callable_: The callable whose parameters to retrieve
    :return: A list of :class:`Parameter` instances
    """
    return list(Signature.from_callable(callable_).parameters.values())


def replace_varargs(
    signature: t.Union[t.Callable[..., T], inspect.Signature],
    remove_parameters: t.Optional[t.Iterable[t.Union[str, int, inspect._ParameterKind]]] = None,
) -> t.Callable[[t.Callable[..., object]], t.Callable[..., T]]:
    def decorator(func: t.Callable[..., T]) -> t.Callable[..., T]:
        merged_signature = Signature.from_callable(func).replace_varargs(signature)

        if remove_parameters:
            merged_signature = merged_signature.without_parameters(*remove_parameters)

        func.__signature__ = merged_signature  # type: ignore
        return func

    return decorator  # type: ignore


# Case 1: No parameters removed, return annotation unchanged
@t.overload
def wraps(
    wrapped_func: t.Callable[P, T],
    *,
    name: t.Optional[str] = None,
    signature: t.Union[None, inspect.Signature, t.Callable] = None,
    remove_parameters: None = None,
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]: ...


# Case 2: No parameters removed, return annotation changed
@t.overload
def wraps(
    wrapped_func: t.Callable[P, t.Any],
    *,
    name: t.Optional[str] = None,
    signature: t.Union[None, inspect.Signature, t.Callable[..., object]] = None,
    remove_parameters: None = None,
    return_annotation: t.Type[T],
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]: ...


# Case 3: Parameters removed, return annotation unchanged
@t.overload
def wraps(
    wrapped_func: t.Callable[..., T],
    *,
    name: t.Optional[str] = None,
    signature: t.Union[None, inspect.Signature, t.Callable[..., object]] = None,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]: ...


# Case 4: Parameters removed, return annotation changed
@t.overload
def wraps(
    wrapped_func: t.Callable[..., t.Any],
    *,
    name: t.Optional[str] = None,
    signature: t.Union[None, inspect.Signature, t.Callable[..., object]] = None,
    remove_parameters: t.Iterable[t.Union[str, int, inspect._ParameterKind]],
    return_annotation: t.Type[T],
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]: ...


def wraps(  # type: ignore
    wrapped_func: t.Callable,
    *,
    name: t.Optional[str] = None,
    signature: t.Union[None, inspect.Signature, t.Callable[..., object]] = None,
    remove_parameters: t.Optional[t.Iterable[t.Union[str, int, inspect._ParameterKind]]] = None,
    return_annotation: Type_ = NONE,  # type: ignore
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
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

    def wrapper(wrapper_func: t.Callable[P, T]) -> t.Callable[P, T]:
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

            wrapper_func.__signature__ = sig  # type: ignore

        return wrapper_func

    return wrapper


def split_arguments(
    signature: t.Union[t.Callable[P, t.Any], Signature, inspect.Signature],
    *args: object,
    **kwargs: object,
) -> t.Tuple[ArgumentBundle[P], ArgumentBundle]:
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

from __future__ import annotations

import collections.abc
import functools
import inspect
import itertools
import types
import typing as t
import typing_extensions as te

from .bound_arguments import BoundArguments
from .parameter import Parameter
from .mark import DOES_NOT_ALTER_SIGNATURE
from .misc import static_mro, static_vars
from ._utils import SIG_EMPTY, NONE, _Sentinel
from .errors import *
from .types import P, TypeAnnotation, ForwardRefContext

__all__ = ["Signature"]


class Signature(inspect.Signature):
    """
    An :class:`inspect.Signature` subclass that represents a function's parameter signature and
    return annotation.

    Instances of this class are immutable.

    .. versionadded:: 1.7.10
        Added ``forward_ref_context`` attribute.

    :ivar parameters: An :class:`OrderedDict` of :class:`Parameter` objects
    :ivar return_annotation: The annotation for the function's return value
    :ivar forward_ref_context: The name of the module where the signature originated from, or `None`.
    """

    __slots__ = ("forward_ref_context",)

    parameters: types.MappingProxyType[str, Parameter]  # type: ignore
    forward_ref_context: t.Optional[ForwardRefContext]

    def __init__(
        self,
        parameters: t.Union[
            t.Iterable[inspect.Parameter], t.Mapping[str, inspect.Parameter], None
        ] = None,
        return_annotation: t.Any = SIG_EMPTY,
        forward_ref_context: t.Optional[ForwardRefContext] = None,
        validate_parameters: bool = True,
    ):
        """
        :param parameters: A list or dict of :class:`Parameter` objects
        :param return_annotation: The annotation for the function's return value
        :param validate_parameters: Whether to check if the signature is valid
        """
        if return_annotation is SIG_EMPTY:
            return_annotation = inspect.Signature.empty

        if parameters is None:
            parameters = ()
        elif isinstance(parameters, collections.abc.Mapping):
            # Unfortunately the `inspect.Signature` constructor only accepts an iterable of
            # parameters, not a dict. So if the user passed in a mapping, we have to discard the
            # keys. At least this ensures that the key and the parameter name are always the same.
            parameters = parameters.values()

        parameters = [Parameter.from_parameter(param) for param in parameters]

        super().__init__(
            parameters,
            return_annotation=return_annotation,
            __validate_parameters__=validate_parameters,
        )

        self.forward_ref_context = forward_ref_context

    def replace(  # type: ignore (invalid override)
        self,
        *,
        parameters: t.Union[
            t.Iterable[inspect.Parameter], t.Mapping[str, inspect.Parameter], None, _Sentinel
        ] = NONE,
        return_annotation: t.Any = NONE,
        forward_ref_context: t.Union[ForwardRefContext, None, _Sentinel] = NONE,
    ) -> te.Self:
        if parameters is NONE:
            parameters = self.parameters

        if return_annotation is NONE:
            return_annotation = self.return_annotation

        if forward_ref_context is NONE:
            forward_ref_context = self.forward_ref_context

        return type(self)(
            parameters=parameters,  # type: ignore
            return_annotation=return_annotation,
            forward_ref_context=forward_ref_context,  # type: ignore
            validate_parameters=False,
        )

    @classmethod
    def from_signature(
        cls,
        signature: inspect.Signature,
    ) -> te.Self:
        """
        Creates an ``introspection.Signature`` instance from an :class:`inspect.Signature` instance.

        :param signature: An :class:`inspect.Signature` instance
        :param Parameter: The class to use for the signature's parameters
        :return: A new ``Signature`` instance
        """
        if isinstance(signature, cls):
            return signature

        params = [Parameter.from_parameter(param) for param in signature.parameters.values()]
        return cls(params, return_annotation=signature.return_annotation)

    @classmethod
    def from_callable(  # type: ignore[incompatible-override]
        cls,
        callable_: t.Callable[P, t.Any],
        *,
        follow_wrapped: bool = True,
        use_signature_db: bool = True,
    ) -> te.Self:
        """
        Returns a matching :class:`Signature` instance for the given ``callable_``.

        Because the signatures of builtin functions often cannot be determined
        (at least in older python versions), this function contains a database
        of signatures for builtin functions. These signatures contain much more
        detail than :func:`inspect.signature` would provide - like type annotations
        and default values of :attr:`Parameter.missing`.

        Pass ``use_signature_db=False`` if you wish to bypass the signature
        database.

        .. versionchanged:: 1.1
            Returns more accurate signatures for builtin functions.
            Also added missing "value" parameter for ``setattr``.

        .. versionadded:: 1.2
            Added ``use_signature_db`` parameter.

        .. versionchanged:: 1.2
            Signature database updated for python 3.9.

        .. versionchanged:: 1.4
            Signature database updated for python 3.10.
            ``param_type`` parameter renamed to ``Parameter``.

        :param callable_: A function or any other callable object
        :param follow_wrapped: Whether to unwrap decorated callables
        :param use_signature_db: Whether to look up the signature
        :return: A corresponding ``Signature`` instance
        :raises InvalidArgumentType: If ``callable_`` isn't a callable object
        :raises NoSignatureFound: If the signature can't be determined (can
            happen for functions defined in C extensions)
        """
        from .signature_db import SIGNATURE_DB

        def recurse(callable_: t.Callable) -> te.Self:
            return cls.from_callable(
                callable_,
                follow_wrapped=follow_wrapped,
                use_signature_db=use_signature_db,
            )

        # Bound methods are annoying pieces of crap that proxy a lot of stuff to the wrapped
        # function. If we carelessly access the `__signature__` or `__wrapped__` attribute, we'll
        # produce incorrect output. So the very first thing we have to do is find out if we're
        # dealing with a bound method.
        if inspect.ismethod(callable_):
            signature = recurse(callable_.__func__)
            return signature.without_parameters(0)  # Remove the first parameter

        # Unwrap the given callable and look it up in the signature database. The signature database
        # often has more accurate signatures than we'd get from `inspect.signature`.
        while True:
            # While we're at it, also look up every callable in the signature database.
            if use_signature_db:
                try:
                    signature = SIGNATURE_DB[callable_]
                except (KeyError, TypeError):
                    pass
                else:
                    return cls.from_signature(SIGNATURE_DB[callable_])

            # If this callable has a cached signature, use that. No need to unwrap further.
            try:
                sig: inspect.Signature = callable_.__signature__  # type: ignore
            except AttributeError:
                pass
            else:
                return cls.from_signature(sig)

            # Are we even supposed to unwrap? If not, abort
            if not follow_wrapped:
                break

            try:
                callable_ = callable_.__wrapped__  # type: ignore
            except AttributeError:
                break

        # Next, find out what kind of callable we're dealing with. There are many that need special
        # handling.

        # First, check if it's a built-in callable. We can't really work with stuff that's written
        # in C, so these need special handling.

        # Is it a class?
        if isinstance(callable_, type):
            # Is it a built-in class?
            if callable_.__module__ == "builtins":
                # Builtin exceptions don't have an accessible signature, but we don't want to
                # hard-code all of them in BUILTIN_SIGNATURES
                if issubclass(callable_, BaseException):  # Note: This includes `Warning`s
                    return cls(
                        [
                            Parameter("args", Parameter.VAR_POSITIONAL),
                        ]
                    )

                return cls._from_builtin_callable(callable_)

            # If the callable_ is a class (one that's written in python, not a builtin class), we
            # must find the function that acts as the constructor. We can't just pass the class
            # itself to `inspect.signature` because
            # 1. We have to ignore methods decorated with `@does_not_alter_signature`
            # 2. In order to resolve the type annotations correctly, we need to know where the
            #    *function* was defined

            # TODO: Instead of simply returning the first function, the most correct behavior would
            # be to merge the signatures of `__new__` and `__init__` (and `__call__`?)
            callable_ = _find_constructor_function(callable_)
            return recurse(callable_)

        # Is it some other kind of built-in callable, i.e. a function, async function, bound method,
        # etc.?
        callable_cls = type(callable_)
        if callable_cls.__module__ == "builtins":
            return cls._from_builtin_callable(callable_)

        # If it's a `functools.partial`, remove the positional parameters and make the keyword
        # parameters optional
        if isinstance(callable_, functools.partial):
            signature = recurse(callable_.func)

            parameters = signature.parameter_list
            for _ in callable_.args:
                if parameters[0].kind >= Parameter.VAR_POSITIONAL:
                    break

                del parameters[0]

            for i, parameter in enumerate(parameters):
                try:
                    default_value = callable_.keywords[parameter.name]
                except KeyError:
                    continue

                parameters[i] = parameter.replace(default=default_value)

            return signature.replace(parameters=parameters)

        # At this point, it must be an object with a `__call__` method.
        fake_self = object.__new__(callable_cls)

        for cls_ in static_mro(callable_cls):
            cls_vars = static_vars(cls_)

            try:
                call = cls_vars["__call__"]
            except KeyError:
                continue

            call = _invoke_descriptor_or_return(call, fake_self, callable_cls)

            if not callable(call):
                break

            return recurse(call)

        raise InvalidArgumentType("callable_", callable_, t.Callable)  # type: ignore

    @classmethod
    def _from_builtin_callable(cls, callable_: t.Callable) -> te.Self:
        try:
            sig = inspect.signature(callable_, follow_wrapped=False)
        except ValueError:
            # Some builtin callables don't have an accessible signature. Nothing we can do about
            # that, so just throw an error.
            raise NoSignatureFound(callable_) from None

        parameters = [Parameter.from_parameter(param) for param in sig.parameters.values()]
        return cls(parameters, sig.return_annotation, forward_ref_context=callable_.__module__)

    @classmethod
    def for_method(
        cls,
        class_or_mro: t.Union[type, t.Iterable[type]],
        method_name: str,
    ) -> te.Self:
        """
        Creates a combined signature for the method in the given class and all
        parent classes, assuming that all `*args` and `**kwargs` are passed to
        the parent method.

        Example::

            class A:
                def method(self, foo: int = 3) -> None:
                    pass

            class B(A):
                def method(self, *args, bar: bool = True, **kwargs):
                    return super().method(*args, **kwargs)

            print(Signature.for_method(B, 'method'))
            # (self, foo: int = 3, *, bar: bool = True) -> None

        .. versionadded:: 1.5
        """
        if isinstance(class_or_mro, type):
            mro = static_mro(class_or_mro)
        else:
            mro = tuple(class_or_mro)

        return_annotation: TypeAnnotation = Signature.empty

        param_lists: t.List[t.List[Parameter]] = []
        for class_ in mro:
            class_vars = static_vars(class_)

            if method_name not in class_vars:
                continue

            method = t.cast(t.Callable[..., object], class_vars[method_name])
            signature = cls.from_callable(method)

            param_lists.append(signature.parameter_list)

            if return_annotation is Signature.empty:
                return_annotation = signature.return_annotation

        if not param_lists:
            raise MethodNotFound(method_name, class_or_mro)

        # Extract the "self" parameter from the first signature, if it has one
        self_param = []
        if param_lists[0]:
            param = param_lists[0][0]

            if param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                self_param = [param]

        positional_params: t.List[Parameter] = []
        keyword_params: t.List[Parameter] = []
        seen: t.Set[str] = set()  # Keep track of parameter names to avoid duplicates
        var_positional: t.Optional[Parameter] = None
        var_keyword: t.Optional[Parameter] = None

        for param_list in param_lists:
            var_positional = None
            var_keyword = None

            for param in param_list:
                # Skip the "self" parameter
                if param is param_list[0] and param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                    continue

                if param.name in seen:
                    continue
                seen.add(param.name)

                if param.kind <= Parameter.POSITIONAL_OR_KEYWORD:
                    positional_params.append(param)
                elif param.kind is Parameter.VAR_POSITIONAL:
                    var_positional = param
                elif param.kind is Parameter.KEYWORD_ONLY:
                    keyword_params.append(param)
                else:
                    var_keyword = param

        # If the last signature has varargs, don't ignore them
        if var_positional is not None:
            positional_params.append(var_positional)

        if var_keyword is not None:
            keyword_params.append(var_keyword)

        # Merge the parameters into a single list and make sure they all have a
        # valid kind
        parameters = self_param + positional_params + keyword_params

        max_kind: inspect._ParameterKind = Parameter.VAR_KEYWORD
        for i, param in reversed(list(enumerate(parameters))):
            if param.kind < max_kind:
                max_kind = param.kind
            elif param.kind > max_kind:
                parameters[i] = param.replace(kind=max_kind)

        return cls(parameters, return_annotation=return_annotation)

    @property
    def parameter_list(self) -> t.List[Parameter]:
        """
        Returns a list of the signature's parameters.
        """
        return list(self.parameters.values())

    @property
    def positional_only_parameters(self) -> t.List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_ONLY`` parameters.
        """
        return [
            param for param in self.parameters.values() if param.kind is Parameter.POSITIONAL_ONLY
        ]

    @property
    def positional_and_keyword_parameters(self) -> t.List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_OR_KEYWORD`` parameters.
        """
        return [
            param
            for param in self.parameters.values()
            if param.kind is Parameter.POSITIONAL_OR_KEYWORD
        ]

    @property
    def keyword_only_parameters(self) -> t.List[Parameter]:
        """
        Returns a list of the signature's ``KEYWORD_ONLY`` parameters.
        """
        return [param for param in self.parameters.values() if param.kind is Parameter.KEYWORD_ONLY]

    @property
    def has_return_annotation(self) -> bool:
        """
        Returns whether the signature's return annotation is not :attr:`Signature.empty`.
        """
        return self.return_annotation is not Signature.empty

    @property
    def num_required_arguments(self) -> int:
        """
        Returns the number of required arguments, i.e. arguments with no default value.
        """
        return sum(not p.is_optional for p in self.parameters.values())

    @property
    def __attributes(self) -> tuple:
        return (self.parameters, self.return_annotation, self.forward_ref_context)

    def __hash__(self) -> int:
        return hash(self.__attributes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, __class__):
            return NotImplemented

        return all(
            self_attr == other_attr
            for self_attr, other_attr in zip(self.__attributes, other.__attributes)
        )

    def bind(self, *args: object, **kwargs: object) -> BoundArguments:
        """
        Similar to :meth:`inspect.Signature.bind`, but returns a
        :class:`introspection.BoundArguments` object.
        """
        bound_args = super().bind(*args, **kwargs)
        return BoundArguments.from_bound_arguments(bound_args)

    def bind_partial(self, *args: object, **kwargs: object) -> BoundArguments:
        """
        Similar to :meth:`inspect.Signature.bind_partial`, but returns a
        :class:`introspection.BoundArguments` object.
        """
        bound_args = super().bind_partial(*args, **kwargs)
        return BoundArguments.from_bound_arguments(bound_args)

    def with_new_parameter(self, index: int, parameter: Parameter) -> te.Self:
        """
        Returns a copy of this signature with a new parameter inserted.

        :param index: The index where the new parameter should be inserted
        :param parameter: The new parameter
        :return: A copy of this signature with the given parameter replaced
        """
        parameters = list(self.parameters.values())
        parameters.insert(index, parameter)
        return self.replace(parameters=parameters)

    def without_parameters(
        self,
        *params_to_remove: t.Union[int, str, inspect._ParameterKind],
    ) -> te.Self:
        """
        Returns a copy of this signature with some parameters removed.

        Parameters can be referenced by the following things:

        1. index
        2. name
        3. kind

        Example::

            >>> sig = Signature([
            ...     Parameter('foo'),
            ...     Parameter('bar'),
            ...     Parameter('baz'),
            ... ])
            >>> sig.without_parameters(0, 'baz')
            <Signature (bar)>

        .. versionchanged:: 1.5
            Parameters can now be referenced by kind.

        :param parameters: Names or indices of the parameters to remove
        :return: A copy of this signature without the given parameters
        """
        to_remove = set(params_to_remove)

        parameters: t.List[Parameter] = []

        for i, param in enumerate(self.parameters.values()):
            if i in to_remove or param.name in to_remove or param.kind in to_remove:
                continue

            parameters.append(param)

        return self.replace(parameters=parameters)

    def replace_varargs(
        self,
        parameters: t.Union[
            t.Callable[..., object],
            inspect.Signature,
            t.Iterable[inspect.Parameter],
            t.Mapping[str, inspect.Parameter],
        ],
    ) -> te.Self:
        """
        Replaces the ``*args`` and/or ``**kwargs`` parameters in this signature
        with the given parameters.

        If this signature has no ``*args``, the new parameters will be made
        ``KEYWORD_ONLY``. If it has no ``**kwargs``, they'll be made
        ``POSITIONAL_ONLY``.
        """
        if isinstance(parameters, inspect.Signature):
            parameters = parameters.parameters.values()
        elif isinstance(parameters, collections.abc.Mapping):
            parameters = parameters.values()
        elif isinstance(parameters, collections.abc.Iterable):
            pass
        else:
            parameters = type(self).from_callable(parameters).parameters.values()

        kinds = {p.kind for p in self.parameters.values()}
        has_varargs = Parameter.VAR_POSITIONAL in kinds
        has_varkwargs = Parameter.VAR_KEYWORD in kinds

        if not has_varargs and not has_varkwargs:
            raise ValueError("This signature has no VAR_POSITIONAL or VAR_KEYWORD parameter")

        # Replace *args with POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, and
        # VAR_POSITIONAL. Replace **kwargs with KEYWORD_ONLY and VAR_KEYWORD.
        replaces_args: t.List[inspect.Parameter] = []
        replaces_kwargs: t.List[inspect.Parameter] = []
        for parameter in parameters:
            # If we have *args but no **kwargs, we'll make all parameters
            # POSITIONAL_ONLY. Similarly, if we have **kwargs but no *args,
            # we'll make them all KEYWORD_ONLY.
            if parameter.kind is Parameter.POSITIONAL_OR_KEYWORD:
                if not has_varargs:
                    parameter = parameter.replace(kind=Parameter.KEYWORD_ONLY)
                elif not has_varkwargs:
                    parameter = parameter.replace(kind=Parameter.POSITIONAL_ONLY)

            if parameter.kind <= Parameter.VAR_POSITIONAL:
                replaces_args.append(parameter)
            else:
                replaces_kwargs.append(parameter)

        merged_parameters: t.List[Parameter] = []
        for parameter in self.parameters.values():
            if parameter.kind is Parameter.VAR_POSITIONAL:
                merged_parameters += map(Parameter.from_parameter, replaces_args)
            elif parameter.kind is Parameter.VAR_KEYWORD:
                merged_parameters += map(Parameter.from_parameter, replaces_kwargs)
            else:
                merged_parameters.append(parameter)

        return type(self)(merged_parameters, return_annotation=self.return_annotation)

    def to_string(
        self,
        implicit_typing: bool = False,
        indent: t.Optional[int] = None,
    ) -> str:
        """
        Returns a string representation of this signature.

        Example::

            >>> Signature([
            ...    Parameter('nums', Parameter.VAR_POSITIONAL, annotation=int)
            ... ], return_annotation=int).to_string()
            '(*nums: int) -> int'

        :param implicit_typing: If ``True``, the "typing." prefix will be
            omitted from types defined in the ``typing`` module
        :return: A string representation of this signature, like you would see
            in python code
        """
        if indent is None:
            indent_str = ""
            sep = ", "
        else:
            indent_str = " " * indent
            sep = ",\n" + indent_str

        grouped_params = {
            kind: list(params)
            for kind, params in itertools.groupby(
                self.parameters.values(),
                key=lambda param: param.kind,
            )
        }

        text_chunks: t.List[str] = []  # When not empty, the last item must always be ``sep``

        # Positional-only parameters with a default value of ``missing`` need
        # special treatment, because they're displayed like [a[, b]]. Even
        # parameters with other default values are enclosed in these brackets:
        # [a, b=5[, c]]
        if Parameter.POSITIONAL_ONLY in grouped_params:
            brackets = 0

            for param in grouped_params.pop(Parameter.POSITIONAL_ONLY):
                param_str = param._to_string(implicit_typing, brackets_and_commas=False)

                if param.default is Parameter.missing:
                    if text_chunks:
                        del text_chunks[-1]
                        param_str = f"[{sep}{param_str}"
                    else:
                        param_str = f"[{param_str}"

                    brackets += 1

                text_chunks += [param_str, sep]

            if brackets:
                text_chunks.insert(-1, "]" * brackets)

            text_chunks += ["/", sep]

        for kind, params in grouped_params.items():
            if kind is Parameter.KEYWORD_ONLY:
                if Parameter.VAR_POSITIONAL not in grouped_params:
                    text_chunks += ["*", sep]

            for param in params:
                param_str = param._to_string(implicit_typing, brackets_and_commas=False)

                if param.default is Parameter.missing:
                    if text_chunks:
                        del text_chunks[-1]
                        param_str = f"[{sep}{param_str}]"
                    else:
                        param_str = f"[{param_str}]"

                text_chunks += [param_str, sep]

        if text_chunks:
            del text_chunks[-1]

            if indent is not None:
                text_chunks.insert(0, f"\n{indent_str}")
                text_chunks.append(",\n")

        params = "".join(text_chunks)

        if self.has_return_annotation:
            from .typing import annotation_to_string

            ann = annotation_to_string(self.return_annotation, implicit_typing=implicit_typing)
            ann = f" -> {ann}"
        else:
            ann = ""

        return f"({params}){ann}"

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        text = self.to_string()

        return "<{} {}>".format(cls_name, text)


def _find_constructor_function(cls: type) -> t.Callable:
    # Find the first function that isn't marked with `@does_not_alter_signature`
    #
    # We don't want the implicit `self` parameter to be included in the signature, so we must return
    # a bound method. But the `@does_not_alter_signature` decorator is applied to the function, so
    # we need both the function and the bound method.
    #
    # Note: Methods don't actually need to be functions. Any descriptor that returns a callable
    # works fine as far as python is concerned. I used the terms "function" and "bound method", but
    # really, we're dealing with a descriptor and whatever that descriptor returned.
    for func, bound_method in _iter_constructor_functions(cls):
        if not callable(bound_method):
            continue

        if func in DOES_NOT_ALTER_SIGNATURE or bound_method in DOES_NOT_ALTER_SIGNATURE:
            continue

        return bound_method

    # If we couldn't find a single constructor function, that means this class doesn't take any
    # arguments.
    return lambda: None


def _iter_constructor_functions(cls: type) -> t.Iterator[t.Tuple[object, object]]:
    # Note: The implicit `self`/`cls` parameter shouldn't show up in the signature, which means we
    # have to return bound methods and not functions.

    metacls = type(cls)

    for metaclass in static_mro(metacls)[:-2]:  # Skip `type` and `object`
        cls_vars = static_vars(metaclass)

        try:
            func = cls_vars["__call__"]
        except KeyError:
            continue

        bound_method = _invoke_descriptor_or_return(func, cls, metacls)
        yield func, bound_method

    # From now on, we need an instance of the class in order to invoke descriptors
    try:
        fake_self = object.__new__(cls)  # type: ignore[wtf]
    except TypeError:
        # This can happen for builtin classes. Just return the class in that case.
        return cls

    mro_vars = [static_vars(cls) for cls in static_mro(cls)[:-1]]  # Skip `object`

    for cls_vars in mro_vars:
        try:
            func = cls_vars["__new__"]
        except KeyError:
            continue

        bound_method = _invoke_descriptor_or_return(func, fake_self, cls)
        yield func, bound_method

    for cls_vars in mro_vars:
        try:
            func = cls_vars["__init__"]
        except KeyError:
            continue

        bound_method = _invoke_descriptor_or_return(func, fake_self, cls)
        yield func, bound_method


T = t.TypeVar("T")


def _invoke_descriptor_or_return(
    descriptor: object, instance: t.Optional[T], owner: t.Optional[t.Type[T]]
) -> t.Callable:
    try:
        get = descriptor.__get__  # type: ignore
    except AttributeError:
        return descriptor  # type: ignore

    return get(instance, owner)

from __future__ import annotations

import collections.abc
import inspect
import itertools
import types
import typing
from typing import *
from typing_extensions import Self

from renumerate import renumerate

from .bound_arguments import BoundArguments
from .parameter import Parameter
from .mark import DOES_NOT_ALTER_SIGNATURE
from .misc import unwrap, static_mro, static_vars, extract_functions
from ._utils import SIG_EMPTY
from .errors import *
from .types import P, TypeAnnotation

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
    forward_ref_context: Optional[str]

    def __init__(
        self,
        parameters: Union[Iterable[Parameter], Mapping[str, Parameter], None] = None,
        return_annotation: Any = SIG_EMPTY,
        forward_ref_context: Optional[str] = None,
        validate_parameters: bool = True,
    ):
        """
        :param parameters: A list or dict of :class:`Parameter` objects
        :param return_annotation: The annotation for the function's return value
        :param validate_parameters: Whether to check if the signature is valid
        """
        if return_annotation is SIG_EMPTY:
            return_annotation = inspect.Signature.empty

        if isinstance(parameters, collections.abc.Mapping):
            parameters = parameters.values()

        # Pyright is dumb and thinks the constructor only accepts Sequences
        parameters = cast(Sequence[Parameter], parameters)

        super().__init__(
            parameters,
            return_annotation=return_annotation,
            __validate_parameters__=validate_parameters,
        )

        self.forward_ref_context = forward_ref_context

    @classmethod
    def from_signature(
        cls,
        signature: inspect.Signature,
    ) -> Self:
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
    def from_callable(
        cls,
        callable_: Callable[P, Any],
        *,
        follow_wrapped: bool = True,
        use_signature_db: bool = True,
    ) -> Self:
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
        :param Parameter: The class to use for the signature's parameters
        :param follow_wrapped: Whether to unwrap decorated callables
        :param use_signature_db: Whether to look up the signature
        :return: A corresponding ``Signature`` instance
        :raises InvalidArgumentType: If ``callable_`` isn't a callable object
        :raises NoSignatureFound: If the signature can't be determined (can
            happen for functions defined in C extensions)
        """
        if use_signature_db:
            from .signature_db import SIGNATURE_DB

            if callable_ in SIGNATURE_DB:
                return cls.from_signature(SIGNATURE_DB[callable_])

        # If the callable_ is a class, it would be incorrect to use its `__module__` as the
        # `forward_ref_context`. We have to find the relevant function (the metaclass's `__call__`,
        # or the `__new__` or the `__init__`) and use *its* `__module__`.
        if isinstance(callable_, type):
            callable_ = cast(Callable[P, Any], _find_constructor_function(callable_))

        ignore_first_parameter = False
        
        if inspect.ismethod(callable_):
            callable_ = callable_.__func__  # type: ignore
            ignore_first_parameter = True

        if follow_wrapped:
            callable_ = unwrap(callable_, lambda func: hasattr(func, "__signature__"))  # type: ignore

        if not callable(callable_):
            raise InvalidArgumentType("callable_", callable_, typing.Callable)

        try:
            sig = inspect.signature(callable_, follow_wrapped=False)
        except ValueError as error:
            # Callables written in C don't have an accessible signature.
            #
            # However, a ValueError can also be raised if `functools.partial` is
            # used to pass invalid arguments to a function, for example:
            #
            # partial(open, hello_kitty=True)
            if not str(error).startswith("no signature found"):
                raise
        else:
            parameters = [Parameter.from_parameter(param) for param in sig.parameters.values()]

            if ignore_first_parameter:
                del parameters[0]

            return cls(parameters, sig.return_annotation, forward_ref_context=callable_.__module__)

        # Builtin exceptions also need special handling, but we don't want to
        # hard-code all of them in BUILTIN_SIGNATURES
        if isinstance(callable_, type) and issubclass(callable_, BaseException):
            return cls(
                [
                    Parameter("args", Parameter.VAR_POSITIONAL),
                ]
            )

        raise NoSignatureFound(callable_)

    @classmethod
    def for_method(
        cls,
        class_or_mro: Union[type, Iterable[type]],
        method_name: str,
    ) -> Self:
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

        param_lists: List[List[Parameter]] = []
        for class_ in mro:
            class_vars = static_vars(class_)

            if method_name not in class_vars:
                continue

            method = cast(Callable[..., object], class_vars[method_name])
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

        positional_params: List[Parameter] = []
        keyword_params: List[Parameter] = []
        seen: Set[str] = set()  # Keep track of parameter names to avoid duplicates
        var_positional: Optional[Parameter] = None
        var_keyword: Optional[Parameter] = None

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
        for i, param in renumerate(parameters):
            if param.kind < max_kind:
                max_kind = param.kind
            elif param.kind > max_kind:
                parameters[i] = param.replace(kind=max_kind)

        return cls(parameters, return_annotation=return_annotation)

    @property
    def parameter_list(self) -> List[Parameter]:
        """
        Returns a list of the signature's parameters.
        """
        return list(self.parameters.values())

    @property
    def positional_only_parameters(self) -> List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_ONLY`` parameters.
        """
        return [
            param for param in self.parameters.values() if param.kind is Parameter.POSITIONAL_ONLY
        ]

    @property
    def positional_and_keyword_parameters(self) -> List[Parameter]:
        """
        Returns a list of the signature's ``POSITIONAL_OR_KEYWORD`` parameters.
        """
        return [
            param
            for param in self.parameters.values()
            if param.kind is Parameter.POSITIONAL_OR_KEYWORD
        ]

    @property
    def keyword_only_parameters(self) -> List[Parameter]:
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

    def __eq__(self, other: Self) -> bool:
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

    def with_new_parameter(self, index: int, parameter: Parameter) -> Self:
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
        *params_to_remove: Union[int, str, inspect._ParameterKind],
    ) -> Self:
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

        parameters: List[Parameter] = []

        for i, param in enumerate(self.parameters.values()):
            if i in to_remove or param.name in to_remove or param.kind in to_remove:
                continue

            parameters.append(param)

        return self.replace(parameters=parameters)

    def replace_varargs(
        self,
        parameters: Union[
            Callable[..., object],
            inspect.Signature,
            Iterable[inspect.Parameter],
            Mapping[str, inspect.Parameter],
        ],
    ) -> Self:
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
        replaces_args: List[inspect.Parameter] = []
        replaces_kwargs: List[inspect.Parameter] = []
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

        merged_parameters: List[Parameter] = []
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
        indent: typing.Optional[int] = None,
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

        text_chunks: List[str] = []  # When not empty, the last item must always be ``sep``

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


def _find_constructor_function(cls: type) -> Callable:
    # Find the first function that isn't marked with `@does_not_alter_signature`
    for func in _iter_constructor_functions(cls):
        if func not in DOES_NOT_ALTER_SIGNATURE:
            return func

    return cls


def _iter_constructor_functions(cls: type) -> Iterator[Callable]:
    metacls = type(cls)

    for metaclass in static_mro(metacls)[:-2]:  # Skip `type` and `object`
        cls_vars = static_vars(metaclass)

        if "__call__" in cls_vars:
            func = _invoke_descriptor_or_return(cls_vars["__call__"], cls, metacls)
            yield func

    # From now on, we need an instance of the class in order to invoke descriptors
    try:
        fake_self = object.__new__(cls)  # type: ignore[wtf]
    except TypeError:
        # This can happen for builtin classes. Just return the class in that case.
        return cls

    mro_vars = [static_vars(cls) for cls in static_mro(cls)[:-1]]  # Skip `object`

    for cls_vars in mro_vars:
        if "__new__" in cls_vars:
            func = _invoke_descriptor_or_return(cls_vars["__new__"], fake_self, cls)
            yield func

    for cls_vars in mro_vars:
        if "__init__" in cls_vars:
            func = _invoke_descriptor_or_return(cls_vars["__init__"], fake_self, cls)
            yield func


def _invoke_descriptor_or_return(
    descriptor: object, instance: Optional[type], owner: Optional[type]
) -> Callable:
    try:
        get = descriptor.__get__  # type: ignore
    except AttributeError:
        return descriptor  # type: ignore

    return get(instance, owner)

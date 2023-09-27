
import collections.abc
import re
import typing
import typing_extensions

from .introspection import get_type_arguments, is_parameterized_generic, get_generic_base_class
from .subtype_check import is_subtype
from .type_compat import to_python
from ..parameter import Parameter
from ..signature import Signature
from .._utils import eval_or_discard
from ..types import Type_

__all__ = ['is_instance']


Type_Variable = typing.TypeVar('Type_Variable', bound=Type_)


def is_instance(obj: typing.Any, type_: Type_Variable) -> typing_extensions.TypeGuard[Type_Variable]:
    """
    Returns whether ``obj`` is an instance of ``type_``. Unlike the builtin
    ``isinstance``, this function supports generics.

    .. warning::
        This function is a work-in-progress and only supports a subset of all
        generic types. If it encounters a type it can't handle, it will throw a
        :exc:`NotImplementedError`.

    .. versionadded:: 1.5
    """
    # Find out if the type has type parameters
    if not is_parameterized_generic(type_):
        if type_ in TESTS:
            test = TESTS[type_]
            return test(obj)
        
        cls = type(type_)
        if cls is typing.TypeVar:
            return _test_typevar(obj, type_)

        return isinstance(obj, type_)
    
    # Extract the generic base type and verify if the object is an instance of
    # that
    base_type = get_generic_base_class(type_)
    base_type = to_python(base_type, strict=False)

    if base_type in GENERIC_BASE_TESTS:
        test = GENERIC_BASE_TESTS[base_type]
        result = test(obj)
    else:
        result = isinstance(obj, base_type)
    
    if not result:
        return False
    
    # Verify the subtypes
    if base_type not in SUBTYPE_TESTS:
        raise NotImplementedError
    
    subtypes = get_type_arguments(type_)

    test = SUBTYPE_TESTS[base_type]
    return test(obj, *subtypes)


def _test_typevar(obj, var):
    if var.__bound__ is not None and not isinstance(obj, var.__bound__):
        return False
    
    if var.__constraints__:
        if not any(is_instance(obj, typ) for typ in var.__constraints__):
            return False
    
    return True


def _test_dict_subtypes(obj, key_type, value_type):
    for key, value in obj.items():
        if not is_instance(key, key_type):
            return False
        
        if not is_instance(value, value_type):
            return False
    
    return True


def _test_tuple_subtypes(obj, *subtypes):
    if len(obj) != len(subtypes):
        return False
    
    return all(
        is_instance(element, typ)
        for element, typ in zip(obj, subtypes)
    )


def _test_type_subtypes(obj, typ):
    return issubclass(obj, typ)


def _test_iterable_subtypes(obj, item_type):
    return all(
        is_instance(item, item_type)
        for item in obj
    )


def _test_annotated_subtypes(obj, typ, *_):
    return is_instance(obj, typ)


def _test_callable_subtypes(obj, param_types, return_type):
    signature = Signature.from_callable(obj)

    if signature.return_annotation is not Signature.empty:
        if not is_subtype(signature.return_annotation, return_type):
            return False
    
    if param_types is ...:
        return all(
            param.kind != Parameter.KEYWORD_ONLY
            for param in signature.parameters.values()
        )
    
    parameters = signature.parameter_list
    i = 0
    for param_type in param_types:
        if i >= len(parameters):
            return False

        param = parameters[i]
        
        if param.kind >= Parameter.KEYWORD_ONLY:
            return False
        
        if param.annotation is not Parameter.empty:
            # Functions are contravariant in their parameters, so the sub- and supertype are swapped here
            if not is_subtype(param_type, param.annotation):
                return False
        
        if param.kind != Parameter.VAR_POSITIONAL:
            i += 1
    
    # If any parameters with no default value remain, it's not a match
    return all(
        param.is_optional
        for param in parameters[i:]
    )


def _test_literal_subtypes(obj, *options):
    return obj in options


def _test_optional_subtypes(obj, typ):
    return obj is None or is_instance(obj, typ)


def _test_union_subtypes(obj, *types):
    return any(
        is_instance(obj, typ)
        for typ in types
    )


def _test_regex_pattern_subtypes(pattern, subtype):
    return isinstance(pattern.pattern, subtype)


def _test_regex_match_subtypes(match, subtype):
    return isinstance(match.string, subtype)


def _return_true(_):
    return True


TESTS = {
    typing.Any: _return_true,
}


GENERIC_BASE_TESTS = eval_or_discard({
    'typing.Literal': _return_true,
    'typing.Optional': _return_true,
    'typing.Union': _return_true,
}, globals())


SUBTYPE_TESTS = eval_or_discard({
    'dict': _test_dict_subtypes,
    'frozenset': _test_iterable_subtypes,
    'list': _test_iterable_subtypes,
    'set': _test_iterable_subtypes,
    'tuple': _test_tuple_subtypes,
    'type': _test_type_subtypes,

    'collections.abc.Callable': _test_callable_subtypes,
    'collections.abc.Iterable': _test_iterable_subtypes,

    'typing.Callable': _test_callable_subtypes,
    'typing.Literal': _test_literal_subtypes,
    'typing.Optional': _test_optional_subtypes,
    'typing.Union': _test_union_subtypes,

    'typing_extensions.Annotated': _test_annotated_subtypes,

    're.Pattern': _test_regex_pattern_subtypes,
    're.Match': _test_regex_match_subtypes,
}, globals())

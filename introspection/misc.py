import builtins
import copy
import inspect
import sys
import types

from collections import defaultdict, deque
from typing import *
from typing_extensions import ParamSpec

from .errors import *

__all__ = [
    "common_ancestor",
    "create_class",
    "resolve_bases",
    "static_vars",
    "static_copy",
    "static_hasattr",
    "static_mro",
    "resolve_identifier",
    "is_sub_qualname",
    "is_abstract",
    "iter_wrapped",
    "unwrap",
    "extract_functions",
    "rename",
    "compile_function",
    "camel_to_snake",
    "snake_to_camel",
]

P = ParamSpec("P")
T = TypeVar("T")


TYPE_GET_DICT = type.__dict__["__dict__"].__get__
TYPE_GET_MRO = type.__dict__["__mro__"].__get__


def create_class(
    name: str,
    bases: Iterable = (),
    attrs: dict = {},
    metaclass: Optional[Callable[..., Type[T]]] = None,
    **kwargs: Any,
) -> Type[T]:
    """
    Creates a new class. This is similar to :func:`types.new_class`, except it
    calls :func:`resolve_bases` even in python versions <= 3.7. (And it has a
    different interface.)

    :param name: The name of the new class
    :param bases: An iterable of bases classes
    :param attrs: A dict of class attributes
    :param metaclass: The metaclass, or ``None``
    :param kwargs: Keyword arguments to pass to the metaclass
    :return: A new class
    """
    if metaclass is not None:
        kwargs.setdefault("metaclass", metaclass)

    resolved_bases = resolve_bases(bases)
    meta, ns, kwds = types.prepare_class(name, resolved_bases, kwargs)

    ns.update(attrs)

    # Note: In types.new_class this is "is not" rather than "!="
    if resolved_bases != bases:
        ns["__orig_bases__"] = bases

    return meta(name, resolved_bases, ns, **kwds)


def resolve_bases(bases: Iterable) -> Tuple[type]:
    """
    Clone/backport of :func:`types.resolve_bases`.

    :param bases: An iterable of bases, which may or may not be classes
    :return: A tuple of base classes
    """
    result = []

    for base in bases:
        if isinstance(base, type):
            result.append(base)
            continue

        try:
            mro_entries = base.__mro_entries__
        except AttributeError:
            result.append(base)
            continue

        new_bases = mro_entries(bases)
        result.extend(new_bases)

    return tuple(result)


@overload
def static_vars(obj: type) -> Mapping[str, object]:
    ...


@overload
def static_vars(obj: object) -> Dict[str, object]:
    ...


def static_vars(obj: object) -> Mapping[str, object]:
    """
    Like :func:`vars`, but bypasses overridden ``__getattribute__`` methods and
    (for the most part) ``__dict__`` descriptors.

    .. warning::
        Currently, if ``obj`` is not a class, there is a chance that a class
        attribute named ``__dict__`` can shadow the real ``__dict__``::

            >>> class Demo: __dict__ = 'oops'
            ...
            >>> static_vars(Demo())
            'oops'

        This is because I can't find a reliable way to access the real
        ``__dict__`` from within python. As far as I can tell, it's only
        possible through the C API.

    :param obj: An object
    :return: The object's ``__dict__``
    :raises ObjectHasNoDict: If the object has no ``__dict__``
    """
    # We'll start by invoking the __dict__ slot from the `type` class. That'll
    # fail with a TypeError if the object is not a class.
    try:
        return TYPE_GET_DICT(obj)
    except TypeError:
        pass

    obj_type = type(obj)

    # If it's not a class, we'll just grab the last __dict__ attribute from the
    # MRO, which will *hopefully* be a slot
    for cls in reversed(static_mro(obj_type)):
        cls_dict = static_vars(cls)

        if "__dict__" not in cls_dict:
            continue

        dict_slot = cls_dict["__dict__"]

        try:
            descriptor_get = dict_slot.__get__
        except AttributeError:
            return dict_slot
        else:
            return descriptor_get(obj, obj_type)

    raise ObjectHasNoDict("obj", obj)


def static_copy(obj: T) -> T:
    """
    Creates a copy of the given object without invoking any of its methods -
    ``__new__``, ``__init__``, ``__copy__`` or anything else.

    How it works:

    1. A new instance of the same class is created by calling
       ``object.__new__(type(obj))``.
    2. If ``obj`` has a ``__dict__``, the new instance's
       ``__dict__`` is updated with its contents.
    3. All values stored in ``__slots__`` (except for ``__dict__``
       and ``__weakref__``) are assigned to the new object.

    An exception are instances of builtin classes - these are copied
    by calling :func:`copy.copy`.

    .. versionadded:: 1.1

    :param obj: The object to copy
    """
    from .classes import iter_slots

    cls = type(obj)

    # We'll check the __module__ attribute for speed and then also
    # make sure the class isn't lying about its module
    if cls.__module__ == "builtins" and cls in vars(builtins).values():
        return copy.copy(obj)

    new_obj = object.__new__(cls)

    try:
        old_dict = static_vars(obj)
    except ObjectHasNoDict:
        pass
    else:
        static_vars(new_obj).update(old_dict)

    for slot_name, slot in iter_slots(cls):
        if slot_name in {"__dict__", "__weakref__"}:
            continue

        try:
            value = slot.__get__(obj, cls)
        except AttributeError:
            pass
        else:
            slot.__set__(new_obj, value)

    return new_obj


def static_hasattr(obj: Any, attr_name: str) -> bool:
    """
    Like the builtin :func:`hasattr`, except it doesn't execute any
    ``__getattr__`` or ``__getattribute__`` functions and also tries to avoid
    invoking descriptors. (See :func:`~introspection.static_vars` for more details.)

    .. versionadded:: 1.4

    :param obj: The object whose attribute you want to find
    :param attr_name: The name of the attribute to find
    """
    try:
        obj_dict = static_vars(obj)
    except ObjectHasNoDict:
        pass
    else:
        if attr_name in obj_dict:
            return True

    for cls in static_mro(type(obj)):
        if attr_name in vars(cls):
            return True

        # Note: There's no need to handle give __slots__ any
        # special treatment, since they create descriptors in
        # the class namespace anyway.

    return False


def static_mro(cls: type) -> Tuple[type, ...]:
    """
    Given a class as input, returns the class's MRO without invoking any
    overridden ``__getattribute__`` methods or ``__mro__`` descriptors.

    .. versionadded:: 1.4

    :param cls: A class
    """
    return TYPE_GET_MRO(cls)


def common_ancestor(classes: Iterable[type]) -> type:
    """
    Finds the closest common parent class of the given classes. If called with
    an empty iterable, :class:`object` is returned.

    :param classes: An iterable of classes
    :return: The given classes' shared parent class
    """
    # How this works:
    # We loop through all classes' MROs, popping off the left-most class from
    # each. We keep track of how many MROs that class appeared in. If it
    # appeared in all MROs, we return it.

    mros = [deque(static_mro(cls)) for cls in classes]
    num_classes = len(mros)
    share_count = defaultdict(int)

    while mros:
        # loop through the MROs
        for mro in mros:
            # pop off the leftmost class
            cls = mro.popleft()
            share_count[cls] += 1

            # if it appeared in every MRO, return it
            if share_count[cls] == num_classes:
                return cls

        # remove empty MROs
        mros = [mro for mro in mros if mro]

    return object


def iter_wrapped(
    function: Union[Callable, staticmethod, classmethod],
    stop: Optional[Callable[[Callable], bool]] = None,
) -> Iterator[Callable]:
    """
    Given a function as input, yields the function and all the functions it
    wraps.

    Unwraps, but does not yield, instances of ``staticmethod`` and
    ``classmethod``.

    If ``stop`` is given, it must be a function that takes a function as input
    and returns a truth value. As soon as ``stop(function)`` returns a truthy
    result, the iteration stops. (``function`` will not be yielded.)

    Note that unlike :func:`unwrap`, this function doesn't raise an exception if
    the input is a bound method.

    .. versionadded:: 1.4

    :param function: The function to unwrap
    :param stop: A predicate function indicating when to stop iterating
    """
    while True:
        while isinstance(function, (staticmethod, classmethod)):
            function = function.__func__

        if stop is not None and stop(function):
            break

        yield function

        if function in (staticmethod, classmethod):
            break

        try:
            function = function.__wrapped__
        except AttributeError:
            break


def unwrap(
    function: Union[Callable, staticmethod, classmethod],
    stop: Optional[Callable[[Callable], bool]] = None,
) -> Callable:
    r"""
    Like :func:`inspect.unwrap`, but always unwraps :class:`staticmethod`\ s and
    :class:`classmethod`\ s. (:func:`inspect.unwrap` only does this since 3.10)

    Also unlike :func:`inspect.unwrap`, this function raises
    :exc:`CannotUnwrapBoundMethod` if the input is a bound method.

    If ``stop`` is given, it must be a function that takes a function as input
    and returns a truth value. As soon as ``stop(function.__wrapped__)`` returns
    a truthy result, the unwrapping stops.

    .. versionadded:: 1.4

    :param function: The function to unwrap
    :param stop: A predicate function indicating when to stop iterating
    """
    if inspect.ismethod(function):
        raise CannotUnwrapBoundMethod(function)

    for function in iter_wrapped(function, stop):
        pass

    return function


FUNCTION_CONTAINER_TYPES = (staticmethod, classmethod, property)


def extract_functions(obj: Union[FUNCTION_CONTAINER_TYPES]) -> List[Callable]:
    """
    Given a :class:`staticmethod`, :class:`classmethod` or :class:`property` as
    input, returns a list of the contained functions::

        >>> extract_functions(staticmethod(foo))
        [<function foo at 0xdeadbeef>]
        >>> extract_functions(property(get, set))
        [<function get at 0xdeadbeef>, <function set at 0xdeadbeef>]
    """
    if isinstance(obj, (staticmethod, classmethod)):
        return [obj.__func__]

    if isinstance(obj, property):
        return [func for func in (obj.fget, obj.fset, obj.fdel) if func is not None]

    raise InvalidArgumentType("obj", obj, Union[FUNCTION_CONTAINER_TYPES])


def is_abstract(obj: Any) -> bool:
    r"""
    Given an object as input, returns whether it is abstract. The following
    types are supported:

    - Functions: These are considered abstract if they have an
      ``__isabstractmethod__`` property with the value ``True``.
    - ``staticmethod``\ s and ``classmethod``\ s: Abstract if the underlying
      function is abstract.
    - ``property``\ s: Abstract if their getter, setter, or deleter is abstract.
    - Classes: Abstract if any of their attributes are abstract.

    .. versionadded:: 1.4

    :param obj: The object to inspect
    """
    if isinstance(obj, FUNCTION_CONTAINER_TYPES):
        return any(is_abstract(func) for func in extract_functions(obj))

    if isinstance(obj, type):
        seen = set()

        for cls in static_mro(obj):
            for name, value in static_vars(cls).items():
                if name in seen:
                    continue
                seen.add(name)

                if is_abstract(value) and not isinstance(value, type):
                    return True

        return False

    return bool(getattr(obj, "__isabstractmethod__", False))


def rename(obj: Any, name: str) -> None:
    """
    Updates the ``__name__`` and ``__qualname__`` of an object.

    .. versionadded:: 1.4

    :param obj: The object to rename
    :param name: The new name for the object
    """
    old_qualname = obj.__qualname__

    obj.__name__ = name
    obj.__qualname__ = old_qualname[: old_qualname.rfind(".") + 1] + name

    # If it's a class, update the qualnames of its methods
    if not isinstance(obj, type):
        return

    prefix = old_qualname + "."

    for attr in static_vars(obj).values():
        # staticmethods and classmethods have their own  __qualname__ that we
        # must update
        if isinstance(attr, (staticmethod, classmethod)):
            functions = [attr.__func__]

            if sys.version_info >= (3, 10):
                functions.append(attr)
        elif isinstance(attr, FUNCTION_CONTAINER_TYPES):
            functions = extract_functions(attr)
        elif hasattr(attr, "__qualname__"):
            functions = [attr]
        else:
            continue

        for func in functions:
            if not func.__qualname__.startswith(prefix):
                continue

            func.__qualname__ = (
                obj.__qualname__ + func.__qualname__[len(old_qualname) :]
            )


def resolve_identifier(identifier: str) -> object:
    """
    Given a string as input, returns the object referenced by it.

    Example::

        >>> resolve_identifier('introspection.Parameter')
        <class 'introspection.parameter.Parameter'>

    Note that this function will not import any modules; the relevant module
    must already be present in :any:`sys.modules`.

    If no matching object can be found, :exc:`NameError` is raised.

    :param identifier: The identifier to resolve
    :returns: The object referenced by the identifier
    :raises InvalidIdentifier: If the identifier doesn't reference anything
    """
    names = identifier.split(".")

    for i in range(len(names)):
        module_name = ".".join(names[:i])

        if module_name not in sys.modules:
            continue

        obj = sys.modules[module_name]
        for name in names[i:]:
            try:
                obj = getattr(obj, name)
            except AttributeError:
                break
        else:
            return obj

    raise InvalidIdentifier(identifier)


def is_sub_qualname(sub_name: str, base_name: str) -> bool:
    """
    Given two dotted names as input, returns whether the first is a child of the
    second.

    Examples::

        >>> is_sub_qualname('foo.bar', 'foo')
        True
        >>> is_sub_qualname('foo', 'foo')
        True
        >>> is_sub_qualname('foo.bar', 'foo.qux')
        False

    .. versionadded:: 1.5
    """
    sub_parts = sub_name.split(".")
    base_parts = base_name.split(".")

    return sub_parts[: len(base_parts)] == base_parts


def compile_function(
    code: Union[str, Iterable[str]],
    *,
    globals_: Optional[typing.Dict[str, object]] = None,
    allow_builtins: bool = True,
    file_name: str = "<string>",
    **kwargs,
) -> Callable:
    if globals_ is None:
        globals_ = {}

    if allow_builtins:
        globals_ = {
            "__builtins__": builtins,
            **globals_,
        }

    if not isinstance(code, str):
        code = "\n".join(code)

    code_obj = compile(code, file_name, "exec", **kwargs)

    predefined_globals = set(globals_)
    exec(code_obj, globals_)

    for name in globals_.keys() - predefined_globals:
        obj = globals_[name]

        if isinstance(obj, types.FunctionType):
            return obj

    raise ValueError("No function found in code")


def camel_to_snake(camel: str) -> str:
    """
    Converts a camel-case name to a snake-case name.

    Examples::

        >>> camel_to_snake('FooBar')
        'foo_bar'
        >>> camel_to_snake('HTTPAdapater')
        'http_adapter'

    .. versionadded:: 1.5
    """
    chars = []
    last_char_was_upper = True

    for i, char in enumerate(camel):
        is_upper = char.isupper()

        if is_upper:
            char = char.lower()

            if not last_char_was_upper or (
                i > 0 and i + 1 < len(camel) and not camel[i + 1].isupper()
            ):
                chars.append("_")

        chars.append(char)

        last_char_was_upper = is_upper

    return "".join(chars)


def snake_to_camel(snake: str) -> str:
    """
    Converts a snake-case name to a camel-case name.

    Examples::

        >>> snake_to_camel('foo_bar')
        'FooBar'
        >>> snake_to_camel('http_adapter')
        'HttpAdapter'

    .. versionadded:: 1.5
    """
    chars = []
    last_char_was_underscore = True

    for char in snake:
        if char == "_":
            last_char_was_underscore = True
            continue

        if last_char_was_underscore:
            char = char.upper()
            last_char_was_underscore = False

        chars.append(char)

    return "".join(chars)

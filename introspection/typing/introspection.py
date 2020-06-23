
import typing

__all__ = ['is_type', 'is_generic', 'is_generic_class', 'is_qualified_generic', 'is_fully_qualified_generic', 'get_generic_base_class', 'get_type_args', 'get_type_params', 'get_type_name']


if hasattr(typing, '_VariadicGenericAlias'):
    def _is_generic(cls):
        if isinstance(cls, typing._VariadicGenericAlias):
            return True

        try:
            return bool(cls.__parameters__)
        except AttributeError:
            pass

        return cls in {typing.Union, typing.Optional, typing.Literal}

    def _is_generic_class(cls):
        if isinstance(cls, typing._GenericAlias):
            if not cls._special:
                return False
        elif not isinstance(cls, (type, typing._SpecialForm)):
            return False

        return _is_generic(cls)

    def _is_qualified_generic(cls):
        if isinstance(cls, typing._GenericAlias):
            return not cls._special

        return False

    def _is_fully_qualified_generic(cls):
        if isinstance(cls, typing._VariadicGenericAlias):
            return False

        if not isinstance(cls, typing._GenericAlias):
            return False

        return not cls.__parameters__

    def _is_typing_type(cls):
        if isinstance(cls, typing._GenericAlias):
            return True

        try:
            module = cls.__module__
        except AttributeError:
            raise TypeError

        return module == 'typing'

    def _get_generic_base_class(cls):
        if cls._name is not None:
            return getattr(typing, cls._name)

        return cls.__origin__

    def _to_python(cls):
        return getattr(cls, '__origin__', None)

    def _get_name(cls):
        try:
            return cls.__name__
        except AttributeError:
            return cls._name
else:  # python 3.5
    def _is_generic(cls):
        try:
            params = cls.__parameters__
        except AttributeError:
            pass
        else:
            if params:
                return True

        if isinstance(cls, (typing.CallableMeta, typing.TupleMeta, typing._Union)):
            return cls.__args__ is None

        return cls in {typing.Optional}

    def _is_generic_class(cls):
        if isinstance(cls, (typing.CallableMeta, typing._Union)):
            return cls.__args__ is None

        if isinstance(cls, typing.GenericMeta):
            return cls.__args__ is None and bool(cls.__parameters__)

        return cls in {typing.Union, typing.Optional}

    def _is_qualified_generic(cls):
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return cls.__args__ is not None

        return False

    def _is_fully_qualified_generic(cls):
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return cls.__args__ is not None and not cls.__parameters__

        return False

    def _is_typing_type(cls):
        return isinstance(cls, (typing.TypingMeta, typing._TypingBase))

    def _get_generic_base_class(cls):
        return cls.__origin__

    def _to_python(cls):
        return getattr(cls, '__extra__', None)

    def _get_name(cls):
        try:
            return cls.__name__
        except AttributeError:
            pass

        typing_, _, name = repr(cls).partition('.')
        return name


if hasattr(typing, 'get_args'):
    # python 3.8
    def _get_type_args(cls):
        return typing.get_args(cls)
else:
    def _get_type_args(cls):
        # In older python versions, generics only store the
        # last pair of arguments. For instance,
        #    >>> Tuple[List[T]][int].__args__
        #    (int,)
        # The output we want is (List[int],).
        # The _subs_tree() method can help us out: It
        # returns a tuple that we can use to construct
        # the output we want:
        #    >>> Tuple[List[T]][int]._subs_tree()
        #    (typing.Tuple, (typing.List, <class 'int'>))
        base_generic, *subtypes = cls._subs_tree()

        def tree_to_type(tree):
            if isinstance(tree, tuple):
                subtypes = tuple(tree_to_type(t) for t in tree[1:])
                return tree[0][subtypes]

            return tree

        subtypes = tuple(map(tree_to_type, subtypes))

        if base_generic == typing.Callable:
            if subtypes[0] is not ...:
                subtypes = (list(subtypes[:-1]), subtypes[-1])

        return subtypes


def _get_type_params(cls):
    return cls.__parameters__


def _is_protocol(cls):
    return isinstance(cls, typing._ProtocolMeta)


def _get_forward_ref_code(ref):
    return ref.__forward_arg__


def is_type(type_: typing.Any) -> bool:
    """
    Returns whether ``type_`` is a class or a type defined
    in the :module:`typing` module.

    :param type_: The object to examine
    :return: Whether the object is a class or type
    """
    if isinstance(type_, (type, typing.TypeVar)):
        return True

    return is_typing_type(type_, raising=False)


def is_typing_type(type_, raising=True) -> bool:
    """
    Returns whether ``type_`` is a type defined
    in the :module:`typing` module.

    If ``type_`` is not a type as defined by :func:`is_type`
    and ``raising`` is ``True``, a ``TypeError`` is raised.
    (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw a ``TypeError`` on invalid input
    :return: Whether the object is a ``typing`` type
    :raises:
        TypeError: If ``type_`` is not a type and ``raising`` is ``True``
    """
    try:
        return _is_typing_type(type_)
    except TypeError:
        if raising:
            msg = "Expected a class or type, not {!r}"
            raise TypeError(msg.format(type_)) from None
        else:
            return False


def is_generic(type_, raising=True):
    """
    Returns whether ``type_`` is any kind of generic,
    for example ``List`` or ``List[int]``.
    This includes "special" types like ``Union`` and
    ``Tuple`` - anything that's subscriptable is
    considered generic.

    If ``type_`` is not a type as defined by :func:`is_type`
    and ``raising`` is ``True``, a ``TypeError`` is raised.
    (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw a ``TypeError`` on invalid input
    :return: Whether the object is a generic type
    :raises:
        TypeError: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if not is_type(type_):
        if raising:
            msg = "Expected a class or type, not {!r}"
            raise TypeError(msg.format(type_)) from None
        else:
            return False

    return _is_generic(type_)


def is_generic_class(type_, raising=True):
    if _is_generic_class(type_):
        return True

    if raising and not is_type(type_):
        msg = "Expected a class or type, not {!r}"
        raise TypeError(msg.format(type_)) from None
    else:
        return False


def is_base_generic(type_, raising=True):
    """
    Returns whether ``type_`` is a generic base class,
    for example ``List`` (but not ``List[int]``).

    If ``type_`` is not a type as defined by :func:`is_type`
    and ``raising`` is ``True``, a ``TypeError`` is raised.
    (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw a ``TypeError`` on invalid input
    :return: Whether the object is a generic class with no type arguments
    :raises:
        TypeError: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if not is_type(type_):
        if raising:
            msg = "Expected a class or type, not {!r}"
            raise TypeError(msg.format(type_)) from None
        else:
            return False

    return _is_generic_class(type_)


def is_qualified_generic(type_, raising=True):
    if not is_type(type_):
        if raising:
            msg = "Expected a class or type, not {!r}"
            raise TypeError(msg.format(type_)) from None
        else:
            return False

    return _is_qualified_generic(type_)


def is_fully_qualified_generic(type_, raising=True):
    """
    Returns whether ``type_`` is a generic supplied with
    arguments, for example ``List[int]`` (but not ``List``).

    If ``type_`` is not a type as defined by :func:`is_type`
    and ``raising`` is ``True``, a ``TypeError`` is raised.
    (Otherwise, ``False`` is returned.)

    :param type_: The object to examine
    :param raising: Whether to throw a ``TypeError`` on invalid input
    :return: Whether the object is a generic type with type arguments
    :raises:
        TypeError: If ``type_`` is not a type and ``raising`` is ``True``
    """
    if not is_type(type_):
        if raising:
            msg = "Expected a class or type, not {!r}"
            raise TypeError(msg.format(type_)) from None
        else:
            return False

    return _is_fully_qualified_generic(type_)


def get_generic_base_class(type_):
    """
    Given a qualified generic type as input, returns the
    corresponding generic base class.

    Example::

        >>> get_generic_base_class(typing.List[int])
        typing.List

    :param type_: A qualified generic type
    :return: The input type without its type arguments
    """
    if not is_qualified_generic(type_, raising=False):
        msg = '{} is not a qualified typing.Generic and thus has no base'
        raise TypeError(msg.format(type_))

    base = _get_generic_base_class(type_)

    # typing.Optional is a special case that turns into a typing.Union[X, None]
    if base is typing.Union:
        args = _get_type_args(type_)

        if len(args) == 2 and type(None) in args:
            base = typing.Optional

    return base


def get_type_args(type_):
    """
    Given a qualified generic type as input, returns a
    tuple of its type arguments.

    Example::

        >>> get_type_args(typing.List[int])
        (<class 'int'>,)
        >>> get_type_args(typing.Callable[[str], None])
        ([<class 'str'>], None)

    :param type_: A qualified generic type
    :return: The input type's type arguments
    """
    if not is_qualified_generic(type_, raising=False):
        raise TypeError('{} is not a qualified typing.Generic and thus has no type arguments'.format(type_))

    args = _get_type_args(type_)

    # typing.Optional is a special case that turns into a typing.Union[X, None],
    # so we'll remove the `None` argument here
    base = _get_generic_base_class(type_)
    if base is typing.Union:
        NoneType = type(None)

        if NoneType in args:
            args = tuple(arg for arg in args if arg is not NoneType)

    return args


_SPECIAL_TYPE_PARAMS = {
    typing.Union: (typing.TypeVar('T_co', covariant=True),),
    typing.Tuple: (typing.TypeVar('T_co', covariant=True),),
    typing.Callable: (typing.TypeVar('A_contra', contravariant=True),
                      typing.TypeVar('R_co', covariant=True)),
}


def get_type_params(type_):
    """
    Returns the TypeVars of a generic type.

    Examples::

        >>> get_type_params(List)
        (~T,)
        >>> get_type_params(Generator)
        (+T_co, -T_contra, +V_co)

    :param type_:
    :return:
    """
    try:
        return _SPECIAL_TYPE_PARAMS[type_]
    except KeyError:
        pass

    return _get_type_params(type_)


def get_type_name(type_):
    """
    Returns the name of a type.

    Examples::

        >>> get_type_name(list)
        'list'
        >>> get_type_name(typing.List)
        'List'

    :param type_: The type whose name to retrieve
    :return The type's name
    :raises:
        TypeError: If ``type_`` isn't a type or is a qualified generic type
    """
    if not is_type(type_):
        msg = "Expected a class or type, not {!r}"
        raise TypeError(msg.format(type_))

    if is_qualified_generic(type_, raising=False):
        msg = "get_type_name argument must not be a qualified generic type (argument is {!r})"
        raise TypeError(msg.format(type_))

    return _get_name(type_)


Introspecting the ``typing`` module
===================================

.. module:: introspection.typing
.. versionadded:: 1.1
.. deprecated:: 1.2
   The arrival of python 3.9 has made type annotations even more of a mess than they've always been.
   It seems that the devs have completely stopped caring about enforcing incorrect usage of types
   at runtime, allowing us to do a multitude of things that should not be possible, for example:

   - Most types have no idea how many type arguments they should accept::

       >>> list[int, str]
       list[int, str]

   - Some classes that should not accept type arguments at all, do::

       >>> class MyIterable(Iterable[int]): pass
       ... 
       >>> MyIterable[str]
       __main__.MyIterable[str]

   And those are only some of the problems with the 3.9 implementation.

   Supporting typing as implemented in python 3.9 would not only be difficult, but would also
   force me to decide between making my functions return what *is* true vs what *should be*
   true. For example, should ``is_variadic_generic(int)`` return ``True`` or ``False``? What about
   ``is_fully_parameterized_generic(MyIterable)``?

   I don't like either option, so I've decided to drop support for ``typing`` introspection.

The ``introspection.typing`` submodule provides functions for the purpose
of dissecting :mod:`typing` types. It is recommended to familiarize yourself
with the ``typing`` module's core concepts by reading :pep:`0483` before
working with its internals.

|

.. automodule:: introspection.typing.introspection
.. automodule:: introspection.typing.misc
.. automodule:: introspection.typing.type_compat

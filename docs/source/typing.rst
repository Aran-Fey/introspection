
Introspecting the ``typing`` module
===================================

.. module:: introspection.typing
.. versionadded:: 1.1

The ``introspection.typing`` submodule provides functions for the purpose
of dissecting :mod:`typing` types. It is recommended to familiarize yourself
with the ``typing`` module's core concepts by reading :pep:`0483` before
working with its internals.

.. note::
   Sometimes there are discrepancies between what is correct and what the :mod:`typing` module
   actually lets you do. For example, in python 3.9 most types accept an arbitrary number of
   type arguments::

       >>> list[int, str]
       list[int, str]

   In cases like this, where the implementation is more lenient than the specification,
   the functions in this module will return what's correct according to the specification.
   Like so::

       >>> is_variadic_generic(list)
       False

   Other times, the implementation *won't* let you do things that should be possible.
   For example, in python 3.6 it wasn't possible to parameterize a :any:`typing.ClassVar`
   more than once::

       >>> ClassVar[T][int]
       Traceback (most recent call last):
       File "<stdin>", line 1, in <module>
       File "/usr/lib/python3.6/typing.py", line 1404, in __getitem__
           .format(cls.__name__[1:]))
       TypeError: ClassVar cannot be further subscripted
    
   In such cases, this module will respect the limitations of the implementation::

       >>> is_fully_parameterized_generic(ClassVar[T])
       True

|

.. automodule:: introspection.typing.introspection
.. automodule:: introspection.typing.misc
.. automodule:: introspection.typing.type_compat

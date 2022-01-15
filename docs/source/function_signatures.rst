
.. currentmodule:: introspection

Function Signatures
=========================

Function signatures are represented by the :class:`Signature` class.
Function parameters are represented by the :class:`Parameter` class.

Signatures can be created through the :func:`signature` function or the ``Signature`` class's various ``from_X`` methods - :meth:`Signature.from_callable`, :meth:`Signature.from_signature`.

|

.. autoclass:: introspection.Signature
.. autoclass:: introspection.Parameter
.. autoclass:: introspection.BoundArguments
.. autofunction:: introspection.signature

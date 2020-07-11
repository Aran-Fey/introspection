
.. currentmodule:: introspection

Functions related to dundermethods
==============================================

Working with dundermethods can be tricky, because when python searches
for a dundermethod, it doesn't use the same mechanism as it does for
normal attribute access. Normal attribute access like ``obj.attr`` will
look for ``attr`` in the instance's namespace (i.e. ``obj.__dict__``)
and the class's namespace (i.e. ``type(obj).__dict__`` plus the ``__dict__``
of every parent class). Dundermethods, on the other hand, are only
searched for in the class namespace - not the instance namespace.
Defining a dundermethod in the instance namespace won't work::

    class Demo:
        pass

    obj = Demo()
    obj.__len__ = lambda self: 0

    print(len(obj))  # throws TypeError: object of type 'Demo' has no len()

And neither will defining a dundermethod in a metaclass::

    class DemoMeta(type):
        def __len__(cls):
            return 0

    class Demo(metaclass=DemoMeta):
        pass

    obj = Demo()

    print(len(obj))  # throws TypeError: object of type 'Demo' has no len()

So if you wanted to implement your own ``len`` function, you wouldn't have an
easy way of accessing the relevant ``__len__`` method - ``obj.__len__`` would
be incorrect because it would search the instance namespace, and ``type(obj).__len__``
would be incorrect because it would search the metaclass namespace. That's where
these functions come in - ``get_bound_dundermethod(obj)`` or ``get_class_dundermethod(type(obj))``
would do the work for you.

.. automodule:: introspection.dundermethods

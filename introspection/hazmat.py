from .dundermethods import get_class_dundermethod

__all__ = ["super"]


def _get_descriptor(sup: super, name: str):
    cls = sup.__self_class__  # type: ignore
    instance_or_cls = sup.__self__  # type: ignore

    # If it's not a super(cls, instance) situation, abort
    if not isinstance(instance_or_cls, cls):
        raise AttributeError(f"'super' object has no attribute {name}")

    return get_class_dundermethod(type(instance_or_cls), name, start_after=cls)


def _call_descriptor_func(sup: super, attr: str, func_name: str, *args: object) -> None:
    descriptor = _get_descriptor(sup, attr)

    descriptor_func = get_class_dundermethod(type(descriptor), func_name)
    descriptor_func(descriptor, sup.__self__, *args)  # type: ignore


class super(super):
    """
    A subclass of the builtin :any:`python:super` that lets you invoke the setter and
    deleter of descriptors in a parent class.

    .. note::
        Keep in mind that the 0-argument form of ``super()`` is powered by
        magic. Python automatically inserts the relevant arguments if it sees a
        function call that looks exactly like ``super()``.
        ``introspection.super()`` won't work.

        You either have to pass the required arguments manually, or use
        ``from introspection import super``.

    Example::

        from introspection import super

        class Parent:
            @property
            def attr(self):
                return self._attr

            @attr.setter
            def attr(self, value):
                self._attr = value

        class Child(Parent):
            @Parent.attr.setter
            def attr(self, value):
                super().attr = value + 1

    .. versionadded:: 1.4
    """

    def __setattr__(self, attr: str, value: object) -> None:
        _call_descriptor_func(self, attr, "__set__", value)

    def __delattr__(self, attr: str) -> None:
        _call_descriptor_func(self, attr, "__delete__")

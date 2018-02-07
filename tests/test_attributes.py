
from introspection import get_configurable_attributes


class ConstructorAttrs:
    def __init__(self, a, b, c, d, e):
        self.a = a
        self.b = b
        self.c = c


class PropertyAttrs:
    @property
    def x(self):
        return 1

    @x.setter
    def x(self, value):
        pass

    @property
    def y(self):
        return 2


class MixedAttrs:
    def __init__(self, a, b):
        self.a = a
        self._b = b

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._a = value

    @property
    def b(self):
        return self._b


def test_constructor_attrs():
    attrs = get_configurable_attributes(ConstructorAttrs)
    assert attrs == {'a', 'b', 'c', 'd', 'e'}


def test_property_attrs():
    attrs = get_configurable_attributes(PropertyAttrs)
    assert attrs == {'x'}


def test_mixed_attrs():
    attrs = get_configurable_attributes(MixedAttrs)
    assert attrs == {'a', 'b'}

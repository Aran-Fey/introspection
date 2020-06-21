
import pytest

from introspection import *


def test_get_parameters():
    def func(a: int, b=True):
        pass

    sig = Signature.from_callable(func)
    assert get_parameters(func) == sig.param_list


def test_static_vars():
    class Foo:
        def __init__(self):
            self.x = 4

        def __getattribute__(self, item):
            raise ZeroDivisionError

    foo = Foo()
    attrs = static_vars(foo)
    assert attrs == {'x': 4}


@pytest.mark.parametrize('classes,ancestor', [
    ([], object),
    ([str], str),
    ([int, bool], int),
    ([bool, int], int),
    ([int, float], object),
    ([Exception, IndexError, LookupError], Exception),
])
def test_common_ancestor(classes, ancestor):
    anc = common_ancestor(classes)
    assert anc is ancestor


def test_resolve_bases():
    class Fake:
        def __init__(self, mro_entries):
            self.mro_entries = mro_entries

        def __mro_entries__(self, bases):
            return self.mro_entries

    bases = (Fake(()), Fake([list]), int, 5)

    assert resolve_bases(bases) == (list, int, 5)

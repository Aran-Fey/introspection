
import pytest

from introspection import common_ancestor, static_vars


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

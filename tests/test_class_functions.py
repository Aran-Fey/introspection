
from introspection import get_subclasses


def test_get_subclasses():
    class A: pass
    class B(A): pass
    class C(A): pass
    class D(B, C): pass

    assert get_subclasses(A) == {B, C, D}

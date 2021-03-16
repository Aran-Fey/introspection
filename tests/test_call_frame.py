
import pytest

import inspect
from introspection import CallFrame


GLOBAL_FRAME = CallFrame.current()


@pytest.mark.parametrize('orig_frame', [
    inspect.currentframe(),
    CallFrame(inspect.currentframe()),
])
def test_equality(orig_frame):
    frame = CallFrame.from_frame(orig_frame)

    assert frame == orig_frame


def test_inequality():
    frame = CallFrame.current()

    assert frame != 5


def test_get_current_frame():
    frame1 = inspect.currentframe()
    frame2 = CallFrame.current()

    assert frame1 == frame2


def test_parent_type():
    frame = CallFrame.current()

    assert isinstance(frame.parent, CallFrame)


def test_toplevel_frame_has_no_parent():
    frame = inspect.currentframe()

    while frame.f_back is not None:
        frame = frame.f_back

    frame = CallFrame.from_frame(frame)

    assert frame.parent is None


def test_attrs():
    frame1 = inspect.currentframe()
    frame2 = CallFrame.from_frame(frame1)

    assert frame2.parent == frame1.f_back
    assert frame2.locals is frame1.f_locals
    assert frame2.globals is frame1.f_globals
    assert frame2.builtins is frame1.f_builtins
    assert frame2.code_object is frame1.f_code


def test_scope_name():
    frame = CallFrame.current()

    assert frame.scope_name == 'test_scope_name'


def test_global_scope_name():
    assert GLOBAL_FRAME.scope_name == '<module>'


def test_class_scope_name():
    class Class:
        frame = CallFrame.current()

    assert Class.frame.scope_name == 'Class'


# FIXME: This test randomly fails, apparently because of the file
# path being cached in a .pyc file
def test_file_name():
    frame = CallFrame.current()

    assert frame.file_name == __file__


def test_context():
    with CallFrame.current() as frame:
        _ = frame.parent

    with pytest.raises(Exception):
        _ = frame.parent


def test_resolve_local_name():
    x = object()

    frame = CallFrame.current()

    assert frame.resolve_name('x') is x


def test_resolve_global_name():
    frame = CallFrame.current()

    assert frame.resolve_name('pytest') is pytest


def test_resolve_builtin_name():
    frame = CallFrame.current()

    assert frame.resolve_name('int') is int


def test_resolve_nonexistent_name():
    frame = CallFrame.current()

    with pytest.raises(NameError):
        frame.resolve_name('firetruck')


def test_get_surrounding_function():
    def func():
        return CallFrame.current()

    frame = func()

    assert frame.get_surrounding_function() is func


def test_get_surrounding_function_replaced():
    def func():
        return CallFrame.current()

    frame = func()

    def func():
        pass

    assert frame.get_surrounding_function() is None


def test_get_surrounding_function_deleted():
    def func():
        return CallFrame.current()

    frame = func()

    del func

    assert frame.get_surrounding_function() is None


def test_get_surrounding_function_no_parent():
    frame = CallFrame.current()

    while frame.parent is not None:
        frame = frame.parent

    # Make sure this doesn't crash
    _ = frame.get_surrounding_function()

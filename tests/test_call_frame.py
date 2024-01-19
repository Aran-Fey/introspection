import inspect
import sys
import types
import pytest

from introspection import CallFrame, errors


def current_frame() -> types.FrameType:
    return inspect.currentframe().f_back  # type: ignore


GLOBAL_FRAME = CallFrame.current()


def test_inequality():
    frame = CallFrame.current()

    assert frame != 5


def test_get_current_frame():
    frame = CallFrame.current()

    assert frame._frame == current_frame()


def test_parent_type():
    frame = CallFrame.current()

    assert isinstance(frame.parent, CallFrame)


def test_toplevel_frame_has_no_parent():
    frame = current_frame()

    while frame.f_back is not None:
        frame = frame.f_back

    frame = CallFrame(frame)

    assert frame.parent is None


def test_attrs():
    frame1 = current_frame()
    frame2 = CallFrame(frame1)

    assert frame2.parent == frame1.f_back
    assert frame2.locals is frame1.f_locals
    assert frame2.globals is frame1.f_globals
    assert frame2.builtins is frame1.f_builtins
    assert frame2.code_object is frame1.f_code


def test_scope_name():
    frame = CallFrame.current()

    assert frame.scope_name == "test_scope_name"


def test_global_scope_name():
    assert GLOBAL_FRAME.scope_name == "<module>"


def test_class_scope_name():
    class Class:
        frame = CallFrame.current()

    assert Class.frame.scope_name == "Class"


def test_file_name():
    frame = CallFrame.current()

    # On Windows, the capitalization of the drive letter isn't consistent
    if sys.platform == "win32":
        assert frame.file_name[0].lower() == __file__[0].lower()
        assert frame.file_name[1:] == __file__[1:]
    else:
        assert frame.file_name == __file__

    del frame


def test_context():
    with CallFrame.current() as frame:
        _ = frame.parent

    with pytest.raises(Exception):
        _ = frame.parent


def test_resolve_local_name():
    x = object()

    frame = CallFrame.current()

    assert frame.resolve_name("x") is x


def test_resolve_global_name():
    frame = CallFrame.current()

    assert frame.resolve_name("pytest") is pytest


def test_resolve_builtin_name():
    frame = CallFrame.current()

    assert frame.resolve_name("int") is int


def test_resolve_nonexistent_name():
    frame = CallFrame.current()

    error = errors.NameNotAccessibleFromFrame("firetruck", frame)
    with pytest.raises(error):  # type: ignore[pytest-raisin]
        frame.resolve_name("firetruck")

    # Deprecated exception
    with pytest.raises(NameError):
        frame.resolve_name("firetruck")


def _get_frame_for_this_function():
    return CallFrame.current()


def test_get_surrounding_function_global():
    frame = _get_frame_for_this_function()

    assert frame.get_surrounding_function() is _get_frame_for_this_function


def test_get_surrounding_function_local():
    def func():
        return CallFrame.current()

    frame = func()

    assert frame.get_surrounding_function() is func


def test_get_surrounding_function_replaced():
    def func():  # type: ignore
        return CallFrame.current()

    frame = func()

    def func():
        pass

    with pytest.raises(LookupError):
        frame.get_surrounding_function()


def test_get_surrounding_function_deleted():
    def func():
        return CallFrame.current()

    frame = func()

    del func

    with pytest.raises(LookupError):
        frame.get_surrounding_function()


def test_get_surrounding_function_no_function():
    # Since the global frame isn't in a function, this shouldn't return anything
    with pytest.raises(LookupError):
        GLOBAL_FRAME.get_surrounding_function()

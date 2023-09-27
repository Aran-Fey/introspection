import pytest

from introspection import CallStack, CallFrame


def test_get():
    stack = CallStack.current()
    frame = CallFrame.current()

    assert stack[-1] == frame


def test_from_frame():
    frame = CallFrame.current()
    stack = CallStack.from_frame(frame)

    assert stack[-1] == frame


def test_iteration():
    stack = CallStack.current()
    list(stack)


def test_reverse_iteration():
    stack = CallStack.current()
    list(reversed(stack))


def test_len():
    stack = CallStack.current()
    assert len(stack) > 0


def test_indexing():
    stack = CallStack.current()
    frame = CallFrame.current()

    assert frame == stack[-1]


def test_slicing():
    stack = CallStack.current()
    _ = stack[:5]


def test_contains():
    stack = CallStack.current()
    frame = CallFrame.current()

    assert frame in stack


def test_context():
    with CallStack.current() as stack:
        assert len(stack) > 0

    with pytest.raises(Exception):
        len(stack)

import inspect
import types
from typing import *
from typing_extensions import Self

from . import errors

__all__ = ["CallFrame"]


# `inspect.currentframe()` is *much* faster than `inspect.stack()`, but may not be available.
# Choose the appropriate implementation.
if inspect.currentframe() is None:

    def get_frame(i: int) -> inspect.FrameInfo:  # type: ignore (override)
        return inspect.stack()[i]

else:

    def get_frame(i: int) -> types.FrameType:  # type: ignore (override)
        frame = inspect.currentframe()

        try:
            for _ in range(i):
                frame = frame.f_back  # type: ignore
        except AttributeError:
            raise IndexError

        if frame is None:
            raise IndexError

        return frame


class CallFrame:
    """
    Represents a call frame - an element of the call stack.
    It keeps track of local and closure variables.

    Note that storing CallFrames in variables can create reference
    cycles where a frame contains a reference to itself. To avoid
    this, CallFrames can be used as context managers - upon exit,
    the reference to the underlying frame object is released::

        with CallFrame.current() as frame:
            ...  # Do stuff with the frame
        # At this point, the frame has become unusable
    """

    __slots__ = ("_frame",)

    def __init__(self, frame: Union[types.FrameType, inspect.FrameInfo]):
        """
        Creates a new ``CallFrame`` from a :data:`types.FrameType` or :cls:`inspect.FrameInfo`
        object.

        :param frame: An existing frame object
        """
        if isinstance(frame, inspect.FrameInfo):
            frame = frame.frame

        self._frame = frame

    @classmethod
    def current(cls) -> Self:
        """
        Retrieves the current call frame.
        """
        return cls.up(1)  # up(1) because we need to skip the implementation of `current`

    @classmethod
    def up(cls, n: int, /) -> Self:
        """
        Retrieves the `n`th frame (from the bottom) from the call stack.

        :raises IndexError: If `n` is larger than the call stack
        """
        return cls(get_frame(n + 2))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, __class__):
            return self._frame == other._frame
        elif isinstance(other, types.FrameType):
            return self._frame == other
        elif isinstance(other, inspect.FrameInfo):
            return self._frame == other.frame
        else:
            return NotImplemented

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        del self._frame

    @property
    def parent(self) -> Optional[Self]:
        """
        Returns the next frame one level higher on the call stack.
        """
        parent = self._frame.f_back
        if parent is None:
            return None

        cls = type(self)
        return cls(parent)

    @property
    def builtins(self) -> Dict[str, Any]:
        """
        Returns the builtins seen by this frame
        """
        return self._frame.f_builtins

    @property
    def globals(self) -> Dict[str, Any]:
        """
        Returns the global scope seen by this frame
        """
        return self._frame.f_globals

    @property
    def locals(self) -> Dict[str, Any]:
        """
        Returns the frame's local variable scope
        """
        return self._frame.f_locals

    @property
    def current_line_number(self) -> int:
        """
        Returns the name of the file in which this frame's code was defined
        """
        return self._frame.f_lineno

    @property
    def code_object(self) -> types.CodeType:
        """
        Returns the code object being executed in this frame
        """
        return self._frame.f_code

    @property
    def file_name(self) -> str:
        """
        Returns the name of the file in which this frame's code was defined
        """
        return self.code_object.co_filename

    @property
    def scope_name(self) -> str:
        """
        Returns the name of the scope in which this frame's code was defined.
        In case of a function, the function's name.
        In case of a class, the class's name.
        In any other case, whichever name the interpreter assigned to that scope.
        """
        return self.code_object.co_name

    def belongs_to(self, function: types.FunctionType) -> bool:
        code_object = getattr(function, "__code__", None)

        if code_object is not self.code_object:
            return False

        return True

    def resolve_name(self, name: str) -> object:
        """
        Resolves a variable name, returning the variable's value.

        .. note:: Closure variables don't have a named associated with them,
                which means they cannot be looked up with this function.

                This includes variables marked as ``nonlocal``.

        :param name: The name of the variable you want to look up
        :return: The value mapped to the given name
        :raises NameNotAccessibleFromFrame: If no matching variable is found
        """
        try:
            return self.locals[name]
        except KeyError:
            pass

        try:
            return self.globals[name]
        except KeyError:
            pass

        try:
            return self.builtins[name]
        except KeyError:
            pass

        raise errors.NameNotAccessibleFromFrame(name, self)

    def get_surrounding_function(self) -> types.FunctionType:
        """
        Finds and returns the function in which the code of this frame was defined.

        If the function can't be found, :exc:``LookupError`` is raised.

        :return: The calling function object
        """

        def iter_candidate_functions() -> Iterator[types.FunctionType]:
            funcname = self.scope_name

            try:
                yield self.globals[funcname]
            except KeyError:
                pass

            frame = self
            while frame.parent is not None:
                frame = frame.parent

                try:
                    yield frame.locals[funcname]
                except KeyError:
                    pass

        for function in iter_candidate_functions():
            if not isinstance(function, types.FunctionType):
                continue

            if self.belongs_to(function):
                return function

        raise LookupError

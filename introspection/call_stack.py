import types
from typing import *
from typing_extensions import Self

from .call_frame import CallFrame


__all__ = ["CallStack"]


class CallStack:
    """
    Represents the call stack - a series of :class:`CallFrame` instances.

    This class can be used like a read-only list. It supports iteration, indexing, membership testing, etc. The root frame is first in the list, at index 0.

    Because holding references to call frames can result in reference cycles,
    it's recommended to use CallStack objects as context managers. Upon exit,
    the frame objects are released and the CallStack becomes empty::

        with CallStack.current() as stack:
            ...  # do something with the stack
        # at this point, len(stack) is 0
    """

    __slots__ = ("_frames",)

    def __init__(self, frames: Iterable[types.FrameType]):
        """
        Creates a new ``CallStack`` from the given frame objects.

        :param frames: An iterable of frame objects, starting with the root frame
        """
        self._frames = [CallFrame(frame) for frame in frames]

    @classmethod
    def current(cls) -> Self:
        """
        Get the current call stack.
        """
        with CallFrame.current() as frame:
            return cls.from_frame(cast(CallFrame, frame.parent))

    @classmethod
    def from_frame(cls, frame: Union[types.FrameType, CallFrame]) -> Self:
        """
        Creates a ``CallStack`` containing ``frame`` and all its parents.

        :param frame: The last frame in the call stack
        :return: A new ``CallStack`` instance
        """
        frame_: Optional[types.FrameType]
        if isinstance(frame, CallFrame):
            frame_ = frame._frame
        else:
            frame_ = frame
        del frame

        frames = [frame_]
        while True:
            frame_ = frame_.f_back
            if frame_ is None:
                break

            frames.append(frame_)

        frames.reverse()

        return cls(frames)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self._frames

    def __iter__(self) -> Iterator[CallFrame]:
        return iter(self._frames)

    def __reversed__(self) -> Iterator[CallFrame]:
        return reversed(self._frames)

    def __getitem__(self, index) -> CallFrame:
        return self._frames[index]

    def __len__(self) -> int:
        return len(self._frames)

    def __contains__(self, frame: CallFrame) -> bool:
        return frame in self._frames

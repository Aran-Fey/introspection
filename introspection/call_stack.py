
import types
from typing import Iterable, Union

from .call_frame import CallFrame


__all__ = ['CallStack']


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
    __slots__ = ('__frames',)

    def __init__(self, frames: Iterable[Union[CallFrame, types.FrameType]]):
        """
        Creates a new ``CallStack`` from the given frame objects.

        :param frames: An iterable of frame objects, starting with the root frame
        """
        self.__frames = [CallFrame.from_frame(frame) for frame in frames]

    @classmethod
    def current(cls) -> 'CallStack':
        """
        Get the current call stack.
        """
        with CallFrame.current() as frame:
            return cls.from_frame(frame.parent)

    @classmethod
    def from_frame(cls, frame) -> 'CallStack':
        """
        Creates a ``CallStack`` containing ``frame`` and all its parents.

        :param frame: The last frame in the call stack
        :return: A new ``CallStack`` instance
        """
        frames = [frame]
        while True:
            frame = frame.f_back
            if frame is None:
                break

            frames.append(frame)

        frames.reverse()

        return cls(frames)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__frames.clear()

    def __iter__(self):
        return iter(self.__frames)

    def __reversed__(self):
        return reversed(self.__frames)

    def __getitem__(self, index):
        return self.__frames[index]

    def __len__(self):
        return len(self.__frames)

    def __contains__(self, frame):
        return frame in self.__frames

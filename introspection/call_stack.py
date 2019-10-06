
from typing import List

from .call_frame import CallFrame


__all__ = ['CallStack']


class CallStack:
    """
    Represents the call stack - a series of :class:`CallFrame` instances.

    This class can be used like a read-only list. It supports iteration, indexing, membership testing, etc.
    """

    def __init__(self, frames: List[CallFrame]):
        self.__frames = frames

    @classmethod
    def get(cls) -> 'CallStack':
        """
        Get the current call stack.
        """
        return cls.from_frame(CallFrame.current())

    @classmethod
    def from_frame(cls, frame) -> 'CallStack':
        """
        Creates a `CallStack` containing *frame* and all its parents.

        :param frame: The last frame in the call stack
        :return: A new `CallStack` instance
        """

        frames = [frame]
        while True:
            frame = frame.f_back
            if frame is None:
                break

            frames.append(frame)

        return cls(frames[::-1])

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

    def __contains__(self, item):
        return item in self.__frames

    @property
    def last_frame(self):
        """
        :return: The last frame on the stack
        """
        return self[-1]

    def get_first_external_frame(self):
        frame = self.last_frame

        try:
            pass
        finally:
            del frame

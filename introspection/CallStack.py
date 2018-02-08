
import inspect

from pathlib import Path
from typing import List

from .CallFrame import CallFrame


__all__ = ['CallStack']


class CallStack:
    def __init__(self, frames: List[CallFrame]):
        self.__frames = frames

    @classmethod
    def get(cls):
        return cls.from_frame(inspect.currentframe())

    @classmethod
    def from_frame(cls, frame):
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
        return self[-1]

    def get_first_external_frame(self):
        frame = self.last_frame

        try:
            pass
        finally:
            del frame

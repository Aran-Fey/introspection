from typing import *

from .types import T, P

__all__ = ["ArgumentBundle"]


class ArgumentBundle(Generic[P]):
    def __init__(self, *args: P.args, **kwargs: P.kwargs):
        self.args = args
        self.kwargs = kwargs

    def call(self, function: Callable[P, T]) -> T:
        return function(*self.args, **self.kwargs)

    def to_string(self, indent: Optional[int] = None) -> str:
        """
        Returns a string representation of the arguments.

        :param indent: The number of spaces to indent each line
        :return: A string representation of the arguments
        """
        chunks: List[str] = []

        for value in self.args:
            chunks.append(repr(value))

        for name, value in self.kwargs.items():
            chunks.append(f"{name}={repr(value)}")

        if indent is None:
            arguments = ", ".join(chunks)
            return f"({arguments})"
        else:
            indent_str = " " * indent
            sep = ",\n" + indent_str
            arguments = sep.join(chunks)
            return f"(\n{indent_str}{arguments},\n)"

    def __repr__(self) -> str:
        cls_name = type(self).__qualname__
        return f"{cls_name}{self}"

    def __str__(self) -> str:
        return self.to_string()

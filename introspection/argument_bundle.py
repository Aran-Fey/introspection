
import inspect
import typing
from typing import Any, Dict, Tuple

__all__ = ['ArgumentBundle']


class ArgumentBundle:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def call(self, function):
        return function(*self.args, **self.kwargs)
    
    def __repr__(self):
        cls_name = type(self).__qualname__
        return f'{cls_name}{self}'
    
    def __str__(self):
        args = [repr(arg) for arg in self.args]

        for name, value in self.kwargs.items():
            args.append(f'{name}={value!r}')

        args = ', '.join(args)
        return f'({args})'


import typing


if hasattr(typing, 'ForwardRef'):
    ForwardRef = typing.ForwardRef
else:
    ForwardRef = typing._ForwardRef

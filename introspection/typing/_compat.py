
import typing


if hasattr(typing, 'ForwardRef'):
    ForwardRef = typing.ForwardRef
else:
    ForwardRef = typing._ForwardRef


if hasattr(typing, 'Protocol'):
    Protocol = typing.Protocol
else:
    Protocol = typing._Protocol

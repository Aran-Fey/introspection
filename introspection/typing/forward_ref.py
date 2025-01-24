import typing as t

from ..types import ForwardReference, ForwardRefContext


__all__ = ["ForwardRef"]


class ForwardRef:
    code: str
    context: ForwardRefContext

    @t.overload
    def __init__(self, code: str, context: ForwardRefContext, /): ...

    @t.overload
    def __init__(self, forward_ref: t.ForwardRef, /): ...

    def __init__(self, code: ForwardReference, context: t.Optional[ForwardRefContext] = None):
        if isinstance(code, t.ForwardRef):
            context = code.__forward_module__
            code = code.__forward_arg__

        self.code = code
        self.context = context  # type: ignore (overloads, sigh)

import typing
import typing_extensions


__all__ = ["DATACLASSES_KW_ONLY", "LITERAL_TYPES"]


try:
    from dataclasses import KW_ONLY as DATACLASSES_KW_ONLY
except Exception:
    DATACLASSES_KW_ONLY = object()


LITERAL_TYPES = (typing_extensions.Literal,)
if hasattr(typing, "Literal"):
    LITERAL_TYPES += (typing.Literal,)

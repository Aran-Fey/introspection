import typing
import typing_extensions as te


__all__ = ["DATACLASSES_KW_ONLY", "LITERAL_TYPES", "TYPE_ALIAS_TYPES", "ANYS"]


try:
    from dataclasses import KW_ONLY as DATACLASSES_KW_ONLY
except Exception:
    DATACLASSES_KW_ONLY = object()


LITERAL_TYPES = (te.Literal,)
if hasattr(typing, "Literal"):
    LITERAL_TYPES += (typing.Literal,)

TYPE_ALIAS_TYPES = ()
if hasattr(typing, "TypeAliasType"):
    TYPE_ALIAS_TYPES += (typing.TypeAliasType,)  # type: ignore


# In python 3.10, `typing.Any` and `typing_extensions.Any` are two distinct objects.
ANYS = (typing.Any, te.Any)

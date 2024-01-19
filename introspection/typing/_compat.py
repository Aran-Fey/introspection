import typing
import typing_extensions


LITERAL_TYPES = (typing_extensions.Literal,)
if hasattr(typing, "Literal"):
    LITERAL_TYPES += (typing.Literal,)

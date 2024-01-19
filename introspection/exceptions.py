import traceback
import warnings
from typing import *

__all__ = [
    "print_exception",
    "warn_from_exception",
]


def print_exception(exception: BaseException) -> None:
    """
    Shorthand for ``traceback.print_exception(type(exc), exc,
    exc.__traceback__)``.

    :param exception: The exception to print
    """
    traceback.print_exception(type(exception), exception, exception.__traceback__)


def warn_from_exception(
    exception: BaseException,
    warning_type: Type[Warning] = UserWarning,
    message: Optional[str] = None,
) -> None:
    """
    Turns the given exception into a warning, forwarding all the relevant
    information to :func:`warnings.warn_explicit`.

    :param warning_type: The class to use for the warning.
    :param message: A message for the warning. Defaults to ``str(exception)``.
    """
    if message is None:
        message = str(exception)

    tb = exception.__traceback__
    if tb is None:
        filename = "<unknown file>"
        lineno = 0
        module_globals = {}
    else:
        frame = tb.tb_frame

        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        module_globals = frame.f_globals

    warnings.warn_explicit(
        message,
        warning_type,
        filename=filename,
        lineno=lineno,
        module=module_globals.get("__name__"),
        registry=module_globals.get("__warningregistry__"),
        module_globals=module_globals,
    )


import inspect


def copy_signature(source_func):
    sig = inspect.signature(source_func)

    def deco(func):
        func.__signature__ = sig

        return func

    return deco


def _annotation_to_string(annotation):
    if isinstance(annotation, type):
        return annotation.__qualname__

    return repr(annotation)

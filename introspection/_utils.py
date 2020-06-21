
import inspect


def copy_signature(source_func):
    sig = inspect.signature(source_func)

    def deco(func):
        func.__signature__ = sig

        return func

    return deco


def _is_typing_type(annotation):
    return getattr(annotation, '__module__', None) == 'typing'


def _annotation_to_string(annotation):
    if _is_typing_type(annotation):
        return repr(annotation)

    if hasattr(annotation, '__qualname__'):
        return annotation.__qualname__

    return repr(annotation)


def _annotation_to_string(annotation):
    if isinstance(annotation, type):
        return annotation.__qualname__

    return repr(annotation)

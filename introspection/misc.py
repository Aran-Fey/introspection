
from collections import defaultdict, deque

from datatypes import is_qualified_generic, get_base_generic, get_subtypes, get_type_name

from . import _parsers

__all__ = ['annotation_to_string', 'common_ancestor', 'eval_annotation', 'static_vars']


def eval_annotation(annotation, module=None):
    parser = _parsers.annotation_parser(module)

    try:
        return parser(annotation)
    except SyntaxError:
        raise ValueError('{!r} is not a valid annotation'.format(annotation)) from None


def annotation_to_string(annotation):
    def process_nested(prefix, elems):
        elems = ', '.join(map(annotation_to_string, elems))
        return '{}[{}]'.format(prefix, elems)
    
    if isinstance(annotation, list):
        return process_nested('', annotation)
    
    if is_qualified_generic(annotation):
        base = get_base_generic(annotation)
        subtypes = get_subtypes(annotation)
        
        prefix = annotation_to_string(base)
        return process_nested(prefix, subtypes)

    if hasattr(annotation, '__module__'):
        if annotation.__module__ == 'builtins':
            return annotation.__qualname__
        elif annotation.__module__ == 'typing':
            return get_type_name(annotation)
        else:
            return '{}.{}'.format(annotation.__module__, annotation.__qualname__)
    
    return repr(annotation)


def static_vars(obj):
    return object.__getattribute__(obj, '__dict__')


def common_ancestor(classes):
    """
    Finds the closest common parent class of the given classes.
    If called with no arguments, :class:`object` is returned.

    :param cls_list: Any number of classes
    :return: The given classes' shared parent class
    """

    # How this works:
    # We loop through all classes' MROs, popping off the left-
    # most class from each. We keep track of how many MROs
    # that class appeared in. If it appeared in all MROs,
    # we return it.

    mros = [deque(cls.__mro__) for cls in classes]
    num_classes = len(mros)
    share_count = defaultdict(int)

    while mros:
        # loop through the MROs
        for mro in mros:
            # pop off the leftmost class
            cls = mro.popleft()
            share_count[cls] += 1

            # if it appeared in every MRO, return it
            if share_count[cls] == num_classes:
                return cls

        # remove empty MROs
        mros = [mro for mro in mros if mro]

    return object

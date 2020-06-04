
from collections import defaultdict, deque


__all__ = ['common_ancestor', 'static_vars']


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

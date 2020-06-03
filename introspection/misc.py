
import inspect

from collections import defaultdict, deque


__all__ = ['common_ancestor', 'static_vars']


def static_vars(obj):
    return object.__getattribute__(obj, '__dict__')


def common_ancestor(*cls_list):
    """
    Finds the closest common parent class of the given classes.
    If called with no arguments, :code:`object` is returned.

    :param cls_list: Any number of classes
    :return: The given classes' shared parent class
    """

    mros = [deque(inspect.getmro(cls)) for cls in cls_list]
    track = defaultdict(int)
    while mros:
        for mro in mros:
            cur = mro.popleft()
            track[cur] += 1

            if track[cur] == len(cls_list):
                return cur

        mros = [mro for mro in mros if mro]

    return object

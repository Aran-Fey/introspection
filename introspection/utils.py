
import inspect

from collections import defaultdict, deque


def common_ancestor(*cls_list):
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

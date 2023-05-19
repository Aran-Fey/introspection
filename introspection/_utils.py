
def eval_or_discard(mapping, namespace=None):
    result = {}

    for key, value in mapping.items():
        try:
            key = eval(key, namespace)
        except AttributeError:
            continue

        result[key] = value
    
    return result


# Sphinx doesn't like it when we use inspect._empty as a default value, so we'll
# use sentinels instead
class _Sentinel:
    def __init__(self, repr_):
        self.repr_ = repr_
    
    def __repr__(self):
        return self.repr_  # pragma: no cover


SIG_EMPTY = _Sentinel('inspect.Signature.empty')
PARAM_EMPTY = _Sentinel('inspect.Parameter.empty')

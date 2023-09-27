
__all__ = []


def _create_functions():
    from .dundermethods import DUNDERMETHOD_NAMES, call_dundermethod

    global_vars = globals()

    def make_dunder(dunder_name):
        def func(instance, *args, **kwargs) -> object:
            return call_dundermethod(instance, dunder_name, *args, **kwargs)
        
        func.__name__ = func.__qualname__ = dunder_name
        return func

    for dunder_name in DUNDERMETHOD_NAMES:
        func = make_dunder(dunder_name)

        non_dunder_name = dunder_name[2:-2]
        global_vars[dunder_name] = global_vars[non_dunder_name] = func

        __all__.extend([dunder_name, non_dunder_name])


_create_functions()
del _create_functions

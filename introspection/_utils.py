
import functools
import inspect
import weakref


def weakref_cache(func):
    """
    (This cache is designed for the functions in the ``introspection.typing.introspection`` module.)
    
    Caches a function's return values based on the first argument. The cached
    input values are weakly referenced.
    
    Example::
    
        @weakref_cache
        def demo_func(foo, bar):
    
    Here, every call to ``demo_func`` with a new value for ``foo`` would be cached.
    The values passed to ``bar`` are completely ignored::
    
        >>> demo_func(int, 'bar')  # first call with foo=int, result is cached
        <some output>
        >>> demo_func(int, None)  # second call with foo=int, cached result is returned
        <the same output as before>
    
    If an input value can't be hashed or weakly referenced, the result of that call
    is not cached.
    """
    sig = inspect.signature(func)
    cache_param = next(iter(sig.parameters))
    
    cache = weakref.WeakKeyDictionary()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound_args = sig.bind(*args, **kwargs)
        cache_key = bound_args.arguments[cache_param]
        
        try:
            return cache[cache_key]
        except (KeyError, TypeError):
            pass
        
        result = func(*args, **kwargs)
        
        # If the cache_key isn't hashable, we simply won't cache this result
        try:
            cache[cache_key] = result
        except TypeError:
            pass

        return result

    return wrapper

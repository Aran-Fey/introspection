
def pytest_make_parametrize_id(config, val, argname):
    # Represent types more accurately than pytest does by default.
    if getattr(val, '__module__', None) == 'typing':
        return repr(val)

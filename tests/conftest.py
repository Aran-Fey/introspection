
import types

try:
    GenericAlias = types.GenericAlias
except:
    GenericAlias = ()

def pytest_make_parametrize_id(config, val, argname):
    # Represent types more accurately than pytest does by default.
    if getattr(val, '__module__', None) == 'typing' or isinstance(val, GenericAlias):
        return repr(val)

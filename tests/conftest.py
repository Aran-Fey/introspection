import pytest

import introspection

import types

try:
    GenericAlias = types.GenericAlias
except:
    GenericAlias = ()


def pytest_make_parametrize_id(config, val, argname):
    # Represent types more accurately than pytest does by default.
    if getattr(val, "__module__", None) == "typing" or isinstance(val, GenericAlias):
        return repr(val)


for cls in introspection.errors.Error.__subclasses__():

    @pytest.register_exception_compare(cls)  # type: ignore (If you get an error here, install pytest-raisin)
    def my_error_compare(exc_actual, exc_expected):
        if vars(exc_actual) != vars(exc_expected):
            raise AssertionError(f"{exc_actual!r} != {exc_expected!r}")

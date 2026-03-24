import pytest

import introspection

import sys
import types
from pathlib import Path

try:
    GenericAlias = types.GenericAlias
except AttributeError:
    GenericAlias = ()


def pytest_ignore_collect(collection_path: Path, config) -> bool | None:
    # Ignore any file ending in '_312.py' if we aren't on 3.12+
    if collection_path.name.endswith("_312.py") and sys.version_info < (3, 12):
        return True

    return None


def pytest_make_parametrize_id(config, val, argname):
    # Represent types more accurately than pytest does by default.
    if getattr(val, "__module__", None) == "typing" or isinstance(val, GenericAlias):
        return repr(val)


for cls in introspection.errors.Error.__subclasses__():

    @pytest.register_exception_compare(cls)  # type: ignore (If you get an error here, install pytest-raisin)
    def my_error_compare(exc_actual, exc_expected):
        if vars(exc_actual) != vars(exc_expected):
            raise AssertionError(f"{exc_actual!r} != {exc_expected!r}")

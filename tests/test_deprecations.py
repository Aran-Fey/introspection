
import pytest

from typing import List

from introspection import Signature, Parameter
from introspection.typing import *


@pytest.mark.parametrize('func, args, kwargs', [
])
def test_deprecation_warning(func, args, kwargs):
    with pytest.warns(DeprecationWarning):
        func(*args, **kwargs)

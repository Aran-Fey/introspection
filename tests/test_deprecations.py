
import pytest

from typing import List

from introspection import Signature, Parameter
from introspection.typing import *


@pytest.mark.parametrize('func, args, kwargs', [
    (is_qualified_generic, [int], {}),
    (is_fully_qualified_generic, [int], {}),
    (get_type_args, [List[str]], {}),
    (get_type_params, [List], {}),
    (Signature.from_signature, [Signature()], {'param_type': Parameter}),
    (Signature.from_callable, [filter], {'param_type': Parameter}),
    (getattr, [Signature(), 'param_list'], {}),
])
def test_deprecation_warning(func, args, kwargs):
    with pytest.warns(DeprecationWarning):
        func(*args, **kwargs)

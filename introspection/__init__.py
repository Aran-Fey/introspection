"""
New and improved introspection functions
"""

__version__ = "1.7.10"

from .parameter import *
from .signature_ import *
from .argument_bundle import *
from .bound_arguments import *
from .call_stack import *
from .call_frame import *
from .exceptions import *

from .classes import *
from .dundermethods import *
from .misc import *
from .misc2 import *
from .hazmat import *

from . import dunder
from . import errors
from . import mark
from . import types

# Make sure a ``from introspection import *`` doesn't import the ``typing``
# submodule
import types as types_

__all__ = [
    name
    for name, obj in globals().items()
    if not isinstance(obj, types_.ModuleType) and not name.startswith("_")
]
del types_

"""
New and improved introspection functions
"""

__version__ = '1.2'

from .parameter import *
from .signature import *
from .call_stack import *
from .call_frame import *

from .convenience import *
from .classes import *
from .dundermethods import *
from .misc import *

# make sure a ``from introspection import *`` doesn't
# import the ``typing`` submodule
import types
__all__ = [
    name for name, obj in globals().items()
    if not isinstance(obj, types.ModuleType)
    and not name.startswith('_')
]
del types

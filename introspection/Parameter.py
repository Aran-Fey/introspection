
import inspect

import datatypes


class Parameter:
    NONE = object()

    def __init__(self, name=None, type=None, default_value=NONE):
        self.name = name
        self.type = type
        self.default_value = default_value

    @classmethod
    def from_parameter(cls, parameter):
        type = parameter.annotation if isinstance(parameter.annotation, (type, datatypes.Type)) else None
        default_value = cls.NONE if parameter.default is inspect.Parameter.empty else parameter.default
        return cls(parameter.name, type, default_value)

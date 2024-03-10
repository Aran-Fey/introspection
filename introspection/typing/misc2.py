from typing import Dict, cast

from .type_info import TypeInfo
from ..misc import static_mro, static_vars
from ..types import TypeAnnotation


__all__ = ["get_type_annotations"]


def get_type_annotations(cls: type) -> Dict[str, TypeInfo]:
    """
    Similar to `typing.get_type_hints`, but returns the annotations as `TypeInfo` objects.
    """
    result: Dict[str, TypeInfo] = {}

    for class_ in static_mro(cls):
        cls_vars = static_vars(class_)
        try:
            annotations = cast(Dict[str, TypeAnnotation], cls_vars["__annotations__"])
        except KeyError:
            continue

        for attr_name, annotation in annotations.items():
            if attr_name not in result:
                result[attr_name] = TypeInfo(annotation, forward_ref_context=class_)

    return result

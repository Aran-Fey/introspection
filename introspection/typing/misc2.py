import sys
import typing as t

if sys.version_info >= (3, 14):
    import annotationlib
else:
    annotationlib = None

from .forward_ref import ForwardRef
from .type_info import TypeInfo
from ..errors import CannotResolveForwardref
from ..misc import static_mro, static_vars
from ..types import TypeAnnotation


__all__ = ["get_type_annotations"]


@t.overload
def get_type_annotations(
    cls: type, *, allow_forwardrefs: t.Literal[False] = False
) -> t.Dict[str, TypeInfo]: ...


@t.overload
def get_type_annotations(
    cls: type, *, allow_forwardrefs: bool
) -> t.Dict[str, t.Union[TypeInfo, ForwardRef]]: ...


def get_type_annotations(  # type: ignore (wtf? Some variance nonsense?)
    cls: type, *, allow_forwardrefs: bool = False
) -> t.Dict[str, t.Union[TypeInfo, ForwardRef]]:
    """
    Similar to `typing.get_type_hints`, but returns the annotations as `TypeInfo` objects.
    """
    result: t.Dict[str, t.Union[TypeInfo, ForwardRef]] = {}

    for class_ in static_mro(cls):
        cls_vars = static_vars(class_)
        try:
            annotations = _get_local_annotations_dict(cls_vars)
        except KeyError:
            continue

        for attr_name, annotation in annotations.items():
            if attr_name in result:
                continue

            try:
                value = TypeInfo(annotation, forward_ref_context=class_)
            except CannotResolveForwardref:
                if not allow_forwardrefs:
                    raise

                value = ForwardRef(annotation, class_)  # type: ignore

            result[attr_name] = value

    return result


def _get_local_annotations_dict(
    cls_dict: t.Mapping[str, t.Any],
) -> t.Dict[str, TypeAnnotation]:
    if annotationlib is not None:
        annotate = annotationlib.get_annotate_from_class_namespace(cls_dict)
        if annotate is not None:
            return annotationlib.call_annotate_function(annotate, annotationlib.Format.FORWARDREF)

    return cls_dict.get("__annotations__", {})

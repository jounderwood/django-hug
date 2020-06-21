import inspect
from typing import Callable, List, Optional, Dict, Any, Type, Mapping, Union

from dataclasses import dataclass
from pydantic import parse_obj_as, confloat, BaseModel, ValidationError as PydanticValidationError

from .constants import EMPTY
from .exceptions import ValidationError
from .utils import camelcase_text


class Body(BaseModel):
    pass


@dataclass
class Arg:
    name: str
    type: Optional[Any]
    default: Any


@dataclass
class Spec:
    args: List[Arg]
    return_type: Any

    body_name: Optional[str]
    body_model: Optional[Type[Body]]

    @property
    def arg_types_map(self):
        return {arg.name: arg.type for arg in self.args}

    @classmethod
    def get(cls, fn: Callable, arg_types_override: Optional[Dict[str, Any]] = None) -> "Spec":
        arg_types_override = arg_types_override or {}
        fn = inspect.unwrap(fn)
        signature = inspect.signature(fn)

        args = []
        body_model = None
        body_name = None

        for name, param in signature.parameters.items():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            annotation = None if param.annotation is EMPTY else param.annotation
            if annotation and issubclass(annotation, Body):
                body_model = annotation
                body_name = name
            else:
                args.append(Arg(name=name, type=arg_types_override.get(name, annotation), default=param.default))

        return cls(args=args, body_name=body_name, body_model=body_model, return_type=signature.return_annotation,)


def get_value(
    name: str,
    path_kwargs: Optional[dict] = None,
    request_body: Optional[Any] = None,
    query: Optional[Mapping] = None,
    camelcased_data: bool = False,
):
    val = EMPTY

    original_name = name
    if camelcased_data:
        name = camelcase_text(name)

    if val is EMPTY and path_kwargs:
        val = path_kwargs.get(name, EMPTY)

    if val is EMPTY:
        val = query.get(name, EMPTY)
    if val is EMPTY and camelcased_data:
        val = query.get(original_name, EMPTY)

    if val is EMPTY and request_body is not None:
        val = request_body.get(name, EMPTY)

    return val


def load_value(value, kind: Optional[Any]):
    if kind is None or kind is EMPTY:
        return value

    return parse_obj_as(kind, value)


def normalize_error_messages(errors: Dict[str, Exception]) -> Dict[str, List[Union[dict, str]]]:
    result = {}
    for field_name, error in errors.items():
        if isinstance(error, PydanticValidationError):
            result[field_name] = error.errors()
        elif isinstance(error, ValidationError):
            result[field_name] = [error.errors or error.msg]
        else:
            result[field_name] = [repr(error)]

    return result

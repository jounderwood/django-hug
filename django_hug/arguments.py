import inspect
import json
from typing import Callable, List, NamedTuple

from django.http import RawPostDataException
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields, Schema

from django_hug import ValidationError
from django_hug.constants import EMPTY, HTTP, ContentTypes
from django_hug.directives import get_directive


class Arg(NamedTuple):
    name: str
    arg_type: type
    default: any


class Spec(NamedTuple):
    args: List[Arg]
    return_type: type

    @property
    def args_map(self):
        return {arg.name: arg.arg_type for arg in self.args}


def get_function_spec(fn: Callable) -> Spec:
    signature = inspect.signature(fn)

    return Spec(
        args=[
            Arg(name=name, arg_type=param.annotation, default=param.default)
            for name, param in signature.parameters.items()
        ],
        return_type=signature.return_annotation,
    )


def get_value(name, request, kwargs=None):
    val = EMPTY

    directive = get_directive(name)
    if directive:
        val = directive(request)

    if val is EMPTY and kwargs:
        val = kwargs.get(name, EMPTY)

    if val is EMPTY:
        val = request.GET.get(name, EMPTY)

    if (
        val is EMPTY
        and request.method.upper() in [HTTP.POST, HTTP.PUT, HTTP.PATCH]
    ):
        if ContentTypes.JSON in request.content_type:
            try:
                # TODO: escape performing json.loads on every argument
                body = json.loads(request.body.decode(request.encoding or "utf-8"))
                val = body.get(name, EMPTY)
            except (ValueError, RawPostDataException):
                pass
        else:
            val = request.POST.get(name, EMPTY)

    return val


def load_value(value, arg_type):
    if not arg_type or arg_type is EMPTY:
        return value

    load_with_marshmallow = _get_method(arg_type, Schema, "load") or _get_method(arg_type, fields.Field, "deserialize")

    if load_with_marshmallow:
        try:
            value = load_with_marshmallow(value)
        except MarshmallowValidationError as e:
            raise ValidationError(e.data) from e
    elif callable(arg_type):
        try:
            value = arg_type(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(e) from e

    return value


def _get_method(arg_type, kls, method_name):
    if isinstance(arg_type, kls):
        method = getattr(arg_type, method_name)
    else:
        method = None

    return method

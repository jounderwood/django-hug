import datetime as dt
import decimal
import inspect
import json
import uuid
from typing import Callable, List, NamedTuple

from django.http import RawPostDataException
from marshmallow import ValidationError
from marshmallow import fields, Schema
from marshmallow.exceptions import SCHEMA

from django_hug.constants import EMPTY, HTTP, ContentTypes
from django_hug.directives import get_directive


TYPE_MAPPING = {
    str: fields.String,
    bytes: fields.String,
    dt.datetime: fields.DateTime,
    int: fields.Integer,
    float: fields.Float,
    uuid.UUID: fields.UUID,
    dt.time: fields.Time,
    dt.date: fields.Date,
    dt.timedelta: fields.TimeDelta,
    decimal.Decimal: fields.Decimal,
}


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
    fn = get_unwrapped_function(fn)
    signature = inspect.signature(fn)

    return Spec(
        args=[
            Arg(name=name, arg_type=param.annotation, default=param.default)
            for name, param in signature.parameters.items()
        ],
        return_type=signature.return_annotation,
    )


def get_unwrapped_function(fn):
    while True:
        wrapped = getattr(fn, "__wrapped__", None)
        if wrapped is None:
            break
        fn = wrapped
    return fn


def get_value(name, request, kwargs=None):
    val = EMPTY

    directive = get_directive(name)
    if directive:
        val = directive(request)

    if val is EMPTY and kwargs:
        val = kwargs.get(name, EMPTY)

    if val is EMPTY:
        val = request.GET.get(name, EMPTY)

    if val is EMPTY and request.method.upper() in [HTTP.POST, HTTP.PUT, HTTP.PATCH]:
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


def load_value(value, kind: Callable, default=EMPTY):
    if not kind or kind is EMPTY:
        return value

    if value is EMPTY:
        if default is EMPTY:
            raise ValidationError("Missing data for required field.")
        else:
            return EMPTY

    if isinstance(kind, Schema):
        value = kind.load(value)
    elif inspect.isclass(kind) and issubclass(kind, Schema):
        value = kind().load(value)
    elif isinstance(kind, fields.Field):
        value = kind.deserialize(value)
    elif inspect.isclass(kind) and issubclass(kind, fields.Field):
        value = kind().deserialize(value)
    elif kind in TYPE_MAPPING:
        value = TYPE_MAPPING[kind]().deserialize(value)
    elif callable(kind):
        try:
            value = kind(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(str(e)) from e

    return value


def normalize_error_messages(field_name, e: ValidationError):
    errors = {}

    normalized_messages = e.normalized_messages()
    if SCHEMA in normalized_messages:
        errors[field_name] = normalized_messages[SCHEMA]  # field
    elif "body" == field_name:  # predefined directive,
        errors = normalized_messages
    else:
        errors[field_name] = normalized_messages

    return errors

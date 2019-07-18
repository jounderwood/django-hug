import datetime as dt
import decimal
import inspect
import json
import uuid
from dataclasses import dataclass
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


@dataclass
class Arg:
    name: str
    type: type
    default: any


@dataclass
class Spec:
    args: List[Arg]
    return_type: type

    @property
    def arg_types_map(self):
        return {arg.name: arg.type for arg in self.args}

    @classmethod
    def get(cls, fn: Callable, arg_types_override=None) -> "Spec":
        arg_types_override = arg_types_override or {}
        fn = cls._get_unwrapped(fn)
        fn = inspect.signature(fn)

        return Spec(
            args=[
                Arg(name=name, type=arg_types_override.get(name, param.annotation), default=param.default)
                for name, param in fn.parameters.items()
                if param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
            ],
            return_type=fn.return_annotation,
        )

    @staticmethod
    def _get_unwrapped(fn):
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


def load_value(value, kind: Callable):
    if not kind or kind is EMPTY:
        return value

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

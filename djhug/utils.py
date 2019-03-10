from collections import namedtuple

import json
from marshmallow import fields, Schema
from typing import Callable, NamedTuple, List
import inspect

from djhug import ValidationError
from djhug.constants import empty


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
        return_type=signature.return_annotation
    )


def get_value(name, request, kwargs=None):
    val = empty

    if kwargs:
        val = kwargs.get(name, empty)

    if val is empty:
        val = request.GET.get(name, empty)
    if val is empty:
        val = request.POST.get(name, empty)
    if val is empty and request.body:
        try:
            body = json.loads(request.body.decode('utf-8'))
            val = body.get(name, empty)
        except ValueError:
            pass

    return val


def load_value(value, arg_type):
    if not arg_type or arg_type is empty:
        return value

    load_with_marshmallow = _get_method(arg_type, Schema, 'load') or _get_method(arg_type, fields.Field, 'deserialize')

    if load_with_marshmallow:
        value = load_with_marshmallow(value)
    elif callable(arg_type):
        try:
            value = arg_type(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(e) from e

    return value


def _get_method(arg_type, kls, method):
    if isinstance(arg_type, kls):
        meth = getattr(arg_type, method)
    elif inspect.isclass(arg_type) and issubclass(arg_type, Schema):
        meth = getattr(arg_type(), method)
    else:
        meth = None

    return meth

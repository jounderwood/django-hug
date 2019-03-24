import inspect
import json
from typing import Callable, NamedTuple, List

from django.http import RawPostDataException
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields, Schema

from django_hug import ValidationError
from django_hug.constants import empty
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
    val = empty

    try:
        val = get_directive(name)(request)
    except KeyError:
        pass

    if val is empty and kwargs:
        val = kwargs.get(name, empty)

    if val is empty:
        val = request.GET.get(name, empty)

    if request.method.upper() in ["POST", "PUT", "PATCH"]:
        if val is empty:
            try:
                body = json.loads(request.body.decode("utf-8"))
                val = body.get(name, empty)
            except (ValueError, RawPostDataException):
                pass

        if val is empty:
            val = request.POST.get(name, empty)

    return val


def load_value(value, arg_type):
    if not arg_type or arg_type is empty:
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


def _get_method(arg_type, kls, method):
    if isinstance(arg_type, kls):
        meth = getattr(arg_type, method)
    elif inspect.isclass(arg_type) and issubclass(arg_type, Schema):
        meth = getattr(arg_type(), method)
    else:
        meth = None

    return meth

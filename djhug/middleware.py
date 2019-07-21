import logging
from collections import Mapping
from typing import Callable, Iterable, TYPE_CHECKING

from django.http import HttpRequest, JsonResponse, HttpResponseNotAllowed
from django.utils.deprecation import MiddlewareMixin
from marshmallow import ValidationError

from djhug.arguments import normalize_error_messages, load_value, get_value
from djhug.constants import VIEW_ATTR_NAME, EMPTY, HTTP
from djhug.exceptions import HttpNotAllowed, Error

if TYPE_CHECKING:
    from djhug.routes import Options

logger = logging.getLogger(__name__)


class ViewWrapper:
    def __init__(self, view):
        self.view = view

    def __call__(self, request, *args, **kwargs):
        return process_view(self.view, request, *args, **kwargs)


class DjhugMiddleware(MiddlewareMixin):
    def process_view(self, request: HttpRequest, view_func: Callable, view_args: Iterable, view_kwargs: Mapping):
        if hasattr(view_func, VIEW_ATTR_NAME):
            return process_view(view_func, request, *view_args, **view_kwargs)


def process_view(fn, request, *args, **kwargs):
    opts = getattr(fn, VIEW_ATTR_NAME)

    try:
        kwargs = process_request(opts, request, **kwargs)
        response = fn(request, *args, **kwargs)
        response = process_response(opts, request, response)
    except (Error, ValidationError) as e:
        response = process_errors(opts, e, request)

    return response


def process_request(opts: "Options", request, *args, **kwargs):
    errors = {}

    if request.method not in opts.accepted_methods:
        raise HttpNotAllowed

    args = opts.spec.args[1:]  # ignore request

    for arg in args:
        val = get_value(arg.name, request, kwargs)
        default = arg.default

        try:
            if val is EMPTY:
                if default is EMPTY:
                    raise ValidationError("Missing data for required field.")
                else:
                    continue

            val = load_value(val, arg.type)
            if val is not EMPTY:
                kwargs[arg.name] = val
        except ValidationError as e:
            errors.update(normalize_error_messages(arg.name, e))

    if errors:
        raise ValidationError(errors)

    return kwargs


def process_response(opts: "Options", request, response):
    if isinstance(response, (dict, list)):
        status = 201 if request.method == HTTP.POST else 200
        response = JsonResponse(response, status=status, safe=False)

    for name, value in opts.response_additional_headers.items():
        response[name] = value

    return response


def process_errors(opts: "Options", e, request):
    # TODO: add custom exceptions formatting
    if isinstance(e, HttpNotAllowed):
        response = HttpResponseNotAllowed(opts.accepted_methods)
    elif isinstance(e, ValidationError):
        response = JsonResponse({"errors": e.messages}, status=400)
    else:
        raise e

    return response

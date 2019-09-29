import logging
from collections import Mapping
from functools import wraps
from typing import Callable, Iterable, TYPE_CHECKING, Optional

from django.http import HttpRequest, HttpResponseNotAllowed, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from marshmallow import ValidationError

from .arguments import normalize_error_messages, load_value, get_value
from .constants import VIEW_ATTR_NAME, EMPTY, HTTP, ContentTypes
from .exceptions import HttpNotAllowed, Error
from .formatters import get_request_parser, get_response_formatter
from .utils import underscore, camelcase

if TYPE_CHECKING:
    from .routes import Options

logger = logging.getLogger(__name__)


class RequestsHandler:
    parse_body_for_methods = HTTP.WITH_BODY

    def __init__(self, view):
        self.view: Callable = view
        self.opts: "Options" = getattr(view, VIEW_ATTR_NAME)

    @classmethod
    def create(cls, view: Callable):
        return wraps(view)(cls(view))

    def process(self, request, *args, **kwargs):
        content_type = request.content_type.split(";")[0].lower()

        try:
            kwargs = self.process_request(request, kwargs, content_type=content_type)
            response = self.view(request, *args, **kwargs)
            response = self.process_response(request, response, content_type)
        except (Error, ValidationError) as e:
            response = self.handle_errors(e, content_type)

        return response

    def process_request(self, request, kwargs, content_type: str):
        opts = self.opts
        errors = {}

        method = request.method.upper()

        if method not in opts.accepted_methods:
            raise HttpNotAllowed

        if opts.spec:
            args = opts.spec.args[1:]  # ignore request
        else:
            args = []

        body = self._get_request_body(request, content_type)

        for arg in args:
            val = get_value(arg.name, request, kwargs, body)
            default = arg.default

            if arg.name == self.opts.body_arg_name and val is EMPTY:
                val = body

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

    def _get_request_body(self, request, content_type) -> Optional[dict]:
        if request.method.upper() not in self.parse_body_for_methods:
            return {}

        parser = self.opts.request_parser or get_request_parser(content_type)

        if not parser:
            logger.warning("Failed to parse request body, parser for %s is not found", content_type)
            raise ValidationError({"body": "Failed to parse request body, parser for %s is not found" % content_type})

        try:
            body = parser(request)
        except (ValueError, ValidationError):
            logger.exception("Failed to parse request body as %s, used parser %s", content_type, parser)
            raise ValidationError({"body": "Failed to parse request body as %s" % content_type})

        if self.opts.underscored_request_data:
            body = underscore(body)

        return body

    def process_response(self, request, response, content_type):
        opts = self.opts

        if not isinstance(response, HttpResponse):
            # FIXME other methods
            status = 201 if request.method == HTTP.POST else 200
            response = self._create_response(content=response, content_type=content_type, status=status)

        for name, value in opts.response_additional_headers.items():
            response[name] = value

        return response

    def _create_response(self, content, content_type, status):
        if self.opts.camelcased_response_data:
            content = camelcase(content)

        formatter = self.opts.response_formatter or get_response_formatter(content_type)

        if not formatter:
            content_type = ContentTypes.TEXT
        else:
            content = formatter(content)

        return HttpResponse(content=content, content_type=content_type, status=status)

    def handle_errors(self, e, content_type):
        # TODO: add custom exceptions formatting
        if isinstance(e, HttpNotAllowed):
            response = HttpResponseNotAllowed(self.opts.accepted_methods)
        elif isinstance(e, ValidationError):
            response = self._create_response(content={"errors": e.messages}, content_type=content_type, status=400)
        else:
            raise e

        return response

    __call__ = process


class DjhugMiddleware(MiddlewareMixin):
    def process_view(self, request: HttpRequest, view_func: Callable, view_args: Iterable, view_kwargs: Mapping):
        if hasattr(view_func, VIEW_ATTR_NAME):
            return RequestsHandler(view_func).process(request, *view_args, **view_kwargs)

import logging
from collections import Mapping
from functools import wraps
from typing import Callable, Iterable, TYPE_CHECKING, Optional

from django.http import HttpRequest, HttpResponseNotAllowed, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .arguments import normalize_error_messages, load_value, get_value
from .constants import VIEW_ATTR_NAME, EMPTY, HTTP
from .content_negotiation import get_request_parser, get_response_renderer, get_renderer_content_type
from .exceptions import HttpNotAllowed, DjhugError, HttpNotAcceptable, ValidationError
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
        renderer = self.opts.response_renderer or get_response_renderer(request)

        try:
            kwargs = self.process_request(request, kwargs)
            response = self.view(request, *args, **kwargs)
            response = self.process_response(request, response, renderer)
        except (DjhugError, ValidationError) as e:
            response = self.handle_errors(e, renderer)

        return response

    __call__ = process

    def process_request(self, request, kwargs):
        opts = self.opts
        errors = {}

        if opts.accepted_methods and request.method.upper() not in opts.accepted_methods:
            raise HttpNotAllowed

        if opts.spec:
            args = opts.spec.args[1:]  # ignore request
        else:
            args = []

        body = self._get_request_body(request)

        if opts.spec.body_model:
            try:
                kwargs[opts.spec.body_name] = opts.spec.body_model.parse_obj(body)
            except Exception as e:
                errors[opts.spec.body_name] = e
                body = {}

        for arg in args:
            val = get_value(
                name=arg.name,
                path_kwargs=kwargs,
                request_body=body,
                query=request.GET.dict(),
                camelcased_data=self.opts.underscored_body_data,
            )
            default = arg.default

            try:
                if val is EMPTY:
                    if default is EMPTY:
                        raise ValidationError(
                            {"loc": [arg.name], "msg": "field required", "type": "value_error.missing"}
                        )
                    else:
                        continue

                val = load_value(val, arg.type)
                if val is not EMPTY:
                    kwargs[arg.name] = val
            except Exception as e:
                errors[arg.name] = e

        if errors:
            raise ValidationError(normalize_error_messages(errors))

        return kwargs

    def _get_request_body(self, request) -> Optional[dict]:
        if request.method.upper() not in self.parse_body_for_methods:
            return {}

        content_type = request.content_type
        parser = self.opts.request_parser or get_request_parser(request)

        if not parser:
            logger.warning("Failed to parse request body, parser for %s is not found", content_type)
            raise HttpNotAcceptable

        try:
            body = parser(request)
        except Exception:
            logger.exception("Failed to parse request body as %s, used parser %s", content_type, parser)
            raise ValidationError(
                {
                    "loc": ["body"],
                    "msg": "failed to parse request body as %s" % content_type,
                    "type": "value_error.parse_error",
                }
            )

        if self.opts.underscored_body_data:
            body = underscore(body)

        return body

    def process_response(self, request, response, renderer):
        opts = self.opts
        status = None

        if isinstance(response, tuple) and isinstance(response[0], int):
            status, response = response

        if not isinstance(response, HttpResponse):
            if status is None:
                status = 201 if request.method == HTTP.POST else 200
            response = self._create_response(content=response, status=status, renderer=renderer)

        for name, value in opts.response_additional_headers.items():
            response[name] = value

        return response

    def _create_response(self, content, status, renderer):
        response_model = self.opts.response_model or (self.opts.responses_map and self.opts.responses_map.get(status))

        if response_model:
            content = response_model(**content).dict()

        if self.opts.camelcased_response_data:
            content = camelcase(content)

        if not renderer:
            content_type = None
        else:
            content_type = get_renderer_content_type(renderer)
            content = renderer(content)

        response_cls = self.opts.response_cls or HttpResponse
        return response_cls(content=content, content_type=content_type, status=status)

    def handle_errors(self, e, renderer):
        # TODO: add custom exceptions formatting
        if isinstance(e, HttpNotAllowed):
            response = HttpResponseNotAllowed(self.opts.accepted_methods)
        elif isinstance(e, HttpNotAcceptable):
            response = HttpResponse(status=406)
        elif isinstance(e, ValidationError):
            response = self._create_response(content={"errors": e.errors}, renderer=renderer, status=400)
        else:
            raise e

        return response


class DjhugMiddleware(MiddlewareMixin):
    def process_view(self, request: HttpRequest, view_func: Callable, view_args: Iterable, view_kwargs: Mapping):
        if hasattr(view_func, VIEW_ATTR_NAME):
            return RequestsHandler(view_func).process(request, *view_args, **view_kwargs)

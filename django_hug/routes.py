import functools
from typing import Callable, Optional, List, Iterable
from urllib.parse import urljoin
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.urls import path as url_path, re_path as url_re_path
from django.utils.functional import cached_property
from marshmallow import ValidationError

from django_hug.arguments import Spec, get_function_spec, get_value, load_value, normalize_error_messages
from django_hug.constants import HTTP, ContentTypes, EMPTY, JsonStyleFormat
from django_hug.exceptions import HttpNotAllowed, Error
from django_hug.format import get_formatter


class route:
    fn: Callable
    spec: Spec

    accept = ContentTypes.JSON
    response_headers: Optional[dict] = None

    def __init__(
        self, response_headers: dict = None, accept: Iterable = HTTP.ALL, format_response=None, format_request=None
    ):
        self.accept = accept
        self.response_headers = response_headers

        self.response_formatter = get_formatter(format_response or getattr(settings, "DJHUG_FORMAT_RESPONSE", None))
        self.request_formatter = get_formatter(format_request or getattr(settings, "DJHUG_FORMAT_REQUEST", None))

    def __call__(self, fn):
        self.fn = fn
        self.spec = get_function_spec(fn)

        return self.callable

    @cached_property
    def callable(self):
        @functools.wraps(self.fn)
        def wrap(request, **kwargs):
            try:
                kwargs = self.process_request(request, **kwargs)
                response = self.fn(request, **kwargs)
                response = self.process_response(request, response)
            except (Error, ValidationError) as e:
                response = self.error_handler(e, request)

            return response

        return wrap

    def process_request(self, request, **kwargs):
        errors = {}

        if request.method not in self.accept:
            raise HttpNotAllowed

        args = self.spec.args[1:]  # ignore request

        for arg in args:
            val = get_value(arg.name, request, kwargs)

            try:
                val = load_value(val, arg.arg_type, default=arg.default)
                if val is not EMPTY:
                    kwargs[arg.name] = val
            except ValidationError as e:
                errors.update(normalize_error_messages(arg.name, e))

        if errors:
            raise ValidationError(errors)

        return kwargs

    def process_response(self, request, response):
        if isinstance(response, (dict, list)):
            status = 201 if request.method == HTTP.POST else 200
            response = JsonResponse(response, status=status, safe=False)

        if self.response_headers:
            for name, value in self.response_headers.items():
                response[name] = value

        return response

    def error_handler(self, e: Error, request):
        # TODO: add custom exceptions formatting
        if isinstance(e, HttpNotAllowed):
            response = HttpResponseNotAllowed(self.accept)
        elif isinstance(e, ValidationError):
            response = JsonResponse({"errors": e.messages}, status=400)
        else:
            raise e

        return response


class _django_route(route):
    __slots__ = ("path_handler",)

    def __init__(self, path: str, kwargs=None, name=None, re=False, prefix=None, **kw):
        self.path_handler = url_re_path if re else url_path

        self.path = self.form_path(path, prefix)
        self.kwargs = kwargs or {}
        self.name = name
        self.prefix = prefix

        super().__init__(**kw)

    def form_path(self, path, prefix):
        if prefix:
            path = urljoin(f"/{prefix.strip('/')}/", path.lstrip("/"))
        return path.lstrip("/")

    @property
    def urlpattern(self):
        return self.path_handler(route=self.path, view=self.callable, kwargs=self.kwargs, name=self.name)


class Routes:
    def __init__(self, prefix: str = None):
        self._routes: List[_django_route] = []
        self.prefix = prefix

    def route(self, *args, **kwargs):
        _route = _django_route(*args, **kwargs, prefix=self.prefix)
        self._routes.append(_route)
        return _route

    def urls(self):
        return [r.urlpattern for r in self._routes]

    def get(self, path, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.GET]
        )

    def post(self, path, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.POST]
        )

    def put(self, path, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.PUT]
        )

    def patch(self, path, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.PATCH]
        )

    def delete(self, path, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.DELETE]
        )

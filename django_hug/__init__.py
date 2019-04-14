import functools
from typing import Callable, Optional, List, Iterable

from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.urls import path as url_path, re_path as url_re_path
from django.utils.functional import cached_property

from django_hug.arguments import Spec, get_function_spec, get_value, load_value
from django_hug.constants import HTTP, ContentTypes, EMPTY
from django_hug.exceptions import HttpNotAllowed, ValidationError, Error


class route:
    fn: Callable
    spec: Spec

    accept = ContentTypes.JSON
    response_headers: Optional[dict] = None

    def __init__(self, response_headers: dict = None, accept: Iterable = HTTP.ALL):
        self.accept = accept
        self.response_headers = response_headers

    def __call__(self, fn=None, *args, **kwargs):
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
            except Error as e:
                response = self.error_handler(e, request)

            return response

        return wrap

    def process_request(self, request, **kwargs):
        errors = {}

        if request.method not in self.accept:
            raise HttpNotAllowed

        args = self.spec.args[1:]  # ignore request

        for arg in args:
            name = arg.name
            val = get_value(arg.name, request, kwargs)

            if val is EMPTY and arg.default is EMPTY:
                errors[name] = "Missing data for required field"
                continue

            if val is not EMPTY:
                try:
                    kwargs[name] = load_value(val, arg.arg_type)
                except ValidationError as e:
                    errors[arg.name] = e.message or e.fields_errors

        if errors:
            raise ValidationError(**errors)

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
            response = JsonResponse({"errors": e.fields_errors}, status=400)
        else:
            raise e

        return response


class Routes:
    __slots__ = ("_routes",)

    def __init__(self):
        self._routes: List[_path_route] = []

    def route(self, *args, **kwargs):
        _route = _path_route(*args, **kwargs)
        self._routes.append(_route)
        return _route

    def urls(self):
        return [r.urlpattern for r in self._routes]

    def get(self, path=None, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.GET]
        )

    def post(self, path=None, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.POST]
        )

    def put(self, path=None, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.PUT]
        )

    def patch(self, path=None, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.PATCH]
        )

    def delete(self, path=None, kwargs=None, name=None, re=False, response_headers=None):
        return self.route(
            path=path, kwargs=kwargs, name=name, re=re, response_headers=response_headers, accept=[HTTP.DELETE]
        )


class _path_route(route):
    __slots__ = ("path_handler",)

    def __init__(self, path=None, kwargs=None, name=None, re=False, **kw):
        self.path_handler = url_re_path if re else url_path

        self.path = path
        self.kwargs = kwargs or {}
        self.name = name

        super().__init__(**kw)

    @property
    def urlpattern(self):
        return self.path_handler(route=self.path, view=self.callable, kwargs=self.kwargs, name=self.name)
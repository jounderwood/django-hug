from dataclasses import dataclass, field
from functools import wraps
from weakref import WeakValueDictionary, proxy

from django.urls import path as url_path, re_path
from typing import List, Callable, Dict, Optional, NamedTuple
from urllib.parse import urljoin

from djhug.arguments import Spec
from djhug.constants import HTTP
from djhug.utils import decorator_with_arguments, import_var

VIEW_ATTR_NAME = "__djhug_options__"


@dataclass
class ViewOptions:
    spec: Spec = None

    accepted_methods: List[str] = field(default_factory=list)
    response_additional_headers: Dict[str, str] = field(default_factory=dict)
    request_converters: List[Callable] = field(default_factory=list)
    response_converters: List[Callable] = field(default_factory=list)

    @classmethod
    def get_or_contribute(cls, fn):
        if hasattr(fn, VIEW_ATTR_NAME):
            options = getattr(fn, VIEW_ATTR_NAME)
        else:
            options = cls()
            setattr(fn, VIEW_ATTR_NAME, options)

        return options

    @classmethod
    def register(cls, fn, args=None):
        opts = cls.get_or_contribute(fn)
        opts.spec = Spec.get(fn, arg_types_override=args)

        return fn

    def add_accepted_methods(self, *methods):
        methods = set(map(lambda x: str(x).upper(), methods))
        self.accepted_methods += [method for method in methods if method not in self.accepted_methods]

    def update_headers(self, **headers):
        self.response_additional_headers.update(headers)

    def add_request_converters(self, *converters):
        self.request_converters += self._clean_converters(self.request_converters, converters)

    def add_response_converters(self, *converters):
        self.response_converters += self._clean_converters(self.response_converters, converters)

    @staticmethod
    def _clean_converters(current_converters, converters):
        return [converter for converter in set(converters) if converter not in current_converters]


@decorator_with_arguments
def route(fn: Callable, *_, args: Optional[Dict[str, any]] = None, **__):
    return ViewOptions.register(fn, args=args)


class Routes:
    __slots__ = ("_registered_views", "prefix")

    _registered_views: List["_RegisteredRoute"]

    class _RegisteredRoute(NamedTuple):
        fn: str
        fn_path: str
        path_handler: Callable
        kwargs: Dict
        path: str
        name: str

    def __init__(self, prefix: Optional[str] = None):
        self.prefix = prefix
        self._registered_views = []

    def route(
        self,
        path: str,
        kwargs: Optional[Dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        prefix: Optional[str] = None,
        args: Optional[Dict[str, any]] = None,
        accept: Optional[str] = None,
        **_,
    ):
        def wrap(fn: Callable):
            fn = ViewOptions.register(fn, args=args)
            if accept:
                opts = ViewOptions.get_or_contribute(fn)
                opts.add_accepted_methods(accept)

            fn_mod = fn.__module__
            fn_name = fn.__name__

            self._registered_views.append(
                self._RegisteredRoute(
                    fn=fn,
                    fn_path=f"{fn_mod}.{fn_name}",
                    kwargs=kwargs or {},
                    path=self._form_path(path, prefix),
                    path_handler=re_path if re else url_path,
                    name=name,
                )
            )
            return fn

        return wrap

    @staticmethod
    def _form_path(path, prefix):
        if prefix:
            path = urljoin(f"/{prefix.strip('/')}/", path.lstrip("/"))
        return path.lstrip("/")

    def get_urlpatterns(self):
        urlpatterns = []
        for v in self._registered_views:
            view = import_var(v.fn_path) or v.fn
            url = v.path_handler(route=v.path, view=view, kwargs=v.kwargs, name=v.name)
            urlpatterns.append(url)

        return urlpatterns

    def get(self, path: str, kwargs: Optional[Dict] = None, name: Optional[str] = None, re: bool = False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.GET)

    def post(self, path: str, kwargs: Optional[Dict] = None, name: Optional[str] = None, re: bool = False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.POST)

    def put(self, path: str, kwargs: Optional[Dict] = None, name: Optional[str] = None, re: bool = False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.PUT)

    def patch(self, path: str, kwargs: Optional[Dict] = None, name: Optional[str] = None, re: bool = False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.PATCH)

    def delete(self, path: str, kwargs: Optional[Dict] = None, name: Optional[str] = None, re: bool = False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.DELETE)

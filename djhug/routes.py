from dataclasses import dataclass, field
from functools import wraps
from weakref import WeakValueDictionary, proxy

from django.urls import path as url_path, re_path
from typing import List, Callable, Dict, Optional, NamedTuple
from urllib.parse import urljoin

from djhug.arguments import Spec
from djhug.constants import HTTP
from djhug.utils import decorator_with_arguments

VIEW_ATTR_NAME = "__djhug_options__"

_list = field(default_factory=list)
_dict = field(default_factory=dict)


@dataclass
class ViewOptions:
    spec: Spec = None

    accepted_methods: List[str] = _list
    response_additional_headers: Dict[str, str] = _dict
    request_converters: List[Callable] = _list
    response_converters: List[Callable] = _list

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
        fn: Callable
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
        **options,
    ):
        def wrap(fn):
            fn = ViewOptions.register(fn, args=args)
            if accept:
                opts = ViewOptions.get_or_contribute(fn)
                opts.add_accepted_methods(accept)

            self._registered_views.append(
                self._RegisteredRoute(
                    fn=fn,
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
        return [v.path_handler(route=v.path, view=v.fn, kwargs=v.kwargs, name=v.name) for v in self._registered_views]

    def get(self, path, kwargs=None, name=None, re=False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.GET)

    def post(self, path, kwargs=None, name=None, re=False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.POST)

    def put(self, path, kwargs=None, name=None, re=False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.PUT)

    def patch(self, path, kwargs=None, name=None, re=False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.PATCH)

    def delete(self, path, kwargs=None, name=None, re=False):
        return self.route(path=path, kwargs=kwargs, name=name, re=re, accept=HTTP.DELETE)

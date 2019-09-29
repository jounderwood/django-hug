from typing import List, Callable, Dict, Optional
from urllib.parse import urljoin

from django.urls import path as url_path, re_path
from django.utils.module_loading import import_string

from .constants import HTTP
from .options import Options
from .requests_handler import RequestsHandler
from .utils import decorator_with_arguments


@decorator_with_arguments
def route(fn: Callable, *_, args: Optional[Dict[str, any]] = None, **__):
    fn = Options.register(fn, args=args)
    return RequestsHandler.create(fn)


class Routes:
    __slots__ = ("_registered_views", "prefix")

    _registered_views: List[Dict]

    def __init__(self, prefix: Optional[str] = None):
        self.prefix = prefix
        self._registered_views = []

    def route(
        self,
        path: str,
        kwargs: Optional[Dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        args: Optional[Dict[str, any]] = None,
        accept: Optional[str] = None,
        **_,
    ):
        def wrap(fn: Callable):
            fn = self._add_djhug_options(fn, args=args, accepted_methods=accept)
            self._registered_views.append(
                {
                    "fn": fn,
                    "fn_path": f"{fn.__module__}.{fn.__name__}",
                    "kwargs": kwargs or {},
                    "path": self._form_path(path),
                    "path_handler": re_path if re else url_path,
                    "name": name,
                }
            )
            return fn

        return wrap

    def get_urlpatterns(self):
        return [self._create_urlpattern(params) for params in self._registered_views]

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

    @staticmethod
    def _add_djhug_options(fn, args=None, accepted_methods=None):
        fn = Options.register(fn, args=args)
        if accepted_methods:
            opts = Options.get_or_contribute(fn)
            opts.add_accepted_methods(accepted_methods)
        return fn

    def _form_path(self, path):
        if self.prefix:
            path = urljoin(f"/{self.prefix.strip('/')}/", path.lstrip("/"))
        return path.lstrip("/")

    @staticmethod
    def _create_urlpattern(params: Dict):
        try:
            view = import_string(params["fn_path"])
        except ImportError:
            view = params["fn"]

        view = RequestsHandler.create(view)

        return params["path_handler"](route=params["path"], view=view, kwargs=params["kwargs"], name=params["name"])

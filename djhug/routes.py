from typing import List, Callable, Dict, Optional, Any, Type, Set
from urllib.parse import urljoin

from dataclasses import dataclass
from django.http.response import HttpResponse
from django.urls import path as url_path, re_path
from django.utils.module_loading import import_string
from pydantic import BaseModel

from .constants import HTTP
from .exceptions import ConfigError
from .options import Options
from .requests_handler import RequestsHandler
from .utils import decorator_with_arguments


@decorator_with_arguments
def route(fn: Callable, *_, **__):
    fn = Options.register(fn)
    return RequestsHandler.create(fn)


@dataclass
class _RegisteredView:
    view: Callable
    view_path: str
    kwargs: dict
    path: str
    resolver: Callable
    name: str


class Routes:
    __slots__ = ("_registered_views", "_registered_views_paths", "prefix")

    _registered_views: List[_RegisteredView]
    _registered_views_paths: Set[str]

    def __init__(self, prefix: Optional[str] = None):
        self.prefix = prefix
        self._registered_views = []
        self._registered_views_paths = set()

    def route(
        self,
        path: str,
        kwargs: Optional[Dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        accept: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
        **_,
    ):
        def wrap(fn: Callable):
            fn = self._add_djhug_options(
                fn, accepted_methods=accept, response_model=response_model, response_cls=response_cls
            )
            view = _RegisteredView(
                view=fn,
                view_path="%s.%s" % (fn.__module__, fn.__name__),
                kwargs=kwargs or {},
                path=self._form_path(path),
                resolver=re_path if re else url_path,
                name=name,
            )
            if view.view_path in self._registered_views_paths:
                raise ConfigError("View %s already registered" % view.view_path)

            self._registered_views_paths.add(view.view_path)
            self._registered_views.append(view)
            return fn

        return wrap

    def get_urlpatterns(self):
        return [self._create_urlpattern(view) for view in self._registered_views]

    def get(
        self,
        path: str,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        return self.route(
            path=path,
            kwargs=kwargs,
            name=name,
            re=re,
            accept=HTTP.GET,
            response_model=response_model,
            response_cls=response_cls,
        )

    def post(
        self,
        path: str,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        return self.route(
            path=path,
            kwargs=kwargs,
            name=name,
            re=re,
            accept=HTTP.POST,
            response_model=response_model,
            response_cls=response_cls,
        )

    def put(
        self,
        path: str,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        return self.route(
            path=path,
            kwargs=kwargs,
            name=name,
            re=re,
            accept=HTTP.PUT,
            response_model=response_model,
            response_cls=response_cls,
        )

    def patch(
        self,
        path: str,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        return self.route(
            path=path,
            kwargs=kwargs,
            name=name,
            re=re,
            accept=HTTP.PATCH,
            response_model=response_model,
            response_cls=response_cls,
        )

    def delete(
        self,
        path: str,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
        re: bool = False,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        return self.route(
            path=path,
            kwargs=kwargs,
            name=name,
            re=re,
            accept=HTTP.DELETE,
            response_model=response_model,
            response_cls=response_cls,
        )

    @staticmethod
    def _add_djhug_options(
        fn,
        accepted_methods=None,
        response_model: Optional[Type[BaseModel]] = None,
        response_cls: Optional[Type[HttpResponse]] = None,
    ):
        fn = Options.register(fn)
        opts = Options.get_or_contribute(fn)
        if accepted_methods:
            opts.add_accepted_methods(accepted_methods)
        if response_model:
            opts.set_response_model(response_model)
        if response_cls:
            opts.set_response_cls(response_cls)
        return fn

    def _form_path(self, path):
        if self.prefix:
            path = urljoin(f"/{self.prefix.strip('/')}/", path.lstrip("/"))
        return path.lstrip("/")

    @staticmethod
    def _create_urlpattern(registered_view: _RegisteredView):
        try:
            # TODO handle same names
            view = import_string(registered_view.view_path)
        except ImportError:
            view = registered_view.view

        view = RequestsHandler.create(view)

        return registered_view.resolver(
            route=registered_view.path, view=view, kwargs=registered_view.kwargs, name=registered_view.name
        )

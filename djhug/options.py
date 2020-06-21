import inspect

from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Type, Set
from typing import List, Dict

from django.http.response import HttpResponse

from .arguments import Spec
from .constants import VIEW_ATTR_NAME
from .exceptions import ConfigError
from .settings import Settings
from .utils import decorator_with_arguments


from pydantic import (
    BaseModel,
    NegativeFloat,
    NegativeInt,
    PositiveFloat,
    PositiveInt,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    constr,
    Field,
)


@dataclass
class Options:
    spec: Optional[Spec] = None

    accepted_methods: Set[str] = field(default_factory=set)
    response_additional_headers: Dict[str, str] = field(default_factory=dict)

    request_parser: Optional[Callable] = None
    response_renderer: Optional[Callable] = None

    response_cls: Optional[Type[HttpResponse]] = None

    response_model: Optional[Type[BaseModel]] = None
    responses_map: Optional[Dict[int, Type[BaseModel]]] = None

    camelcased_response_data: bool = False
    underscored_body_data: bool = False

    def __post_init__(self):
        settings = Settings()

        if settings.response_additional_headers is not None:
            self.response_additional_headers = dict(settings.response_additional_headers)
        if settings.camelcased_response_data is not None:
            self.camelcased_response_data = settings.camelcased_response_data
        if settings.underscored_request_data is not None:
            self.underscored_body_data = settings.underscored_request_data

    @classmethod
    def get_or_contribute(cls, fn: Callable) -> "Options":
        """ Get or add special attribute to function with class `Options` instance and return it """
        if hasattr(fn, VIEW_ATTR_NAME):
            options = getattr(fn, VIEW_ATTR_NAME)
        else:
            options = cls()
            setattr(fn, VIEW_ATTR_NAME, options)

        return options

    @classmethod
    def register(cls, fn: Callable) -> Callable:
        """ Add options to function if not present, parse function signature and add spec to options """
        opts = cls.get_or_contribute(fn)

        if opts.spec is not None:
            raise RuntimeError("Can't create multiple routes for one function")

        opts.spec = Spec.get(fn)

        return fn

    def add_accepted_methods(self, *methods: str):
        self.accepted_methods &= set(map(lambda x: str(x).upper(), methods))

    def update_headers(self, **headers: str):
        self.response_additional_headers.update(headers)

    def set_request_parser(self, parser: Callable):
        if not callable(parser):
            raise ConfigError("Request parser %r must be a callable" % parser)
        self.request_parser = parser

    def set_response_renderer(self, renderer: Callable):
        if not callable(renderer):
            raise ConfigError("Response renderer %r must be a callable" % renderer)
        self.response_renderer = renderer

    def set_response_model(self, model: Type[BaseModel]):
        if not model or not issubclass(model, BaseModel):
            raise ConfigError("Response model must be subclass of pydantic `BaseModel`")
        self.response_model = model

    def set_response_cls(self, response_cls: Type[HttpResponse]):
        self.response_cls = response_cls

    def set_response_models_map(self, models: Optional[Dict[int, Type[BaseModel]]]):
        # if not models or not issubclass(model, BaseModel):
        #     raise ValueError("Response model mast be subclass of pydantic `BaseModel`")
        self.responses_map = models


def _get_or_contribute(fn: Callable):
    return Options.get_or_contribute(inspect.unwrap(fn))


@decorator_with_arguments
def with_camelcased_response_data(fn: Callable):
    _get_or_contribute(fn).camelcased_response_data = True
    return fn


@decorator_with_arguments
def with_underscored_body_data(fn: Callable):
    _get_or_contribute(fn).underscored_body_data = True
    return fn


def with_request_parser(formatter: Callable):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).set_request_parser(formatter)
        return fn

    return wrapper


def with_response_renderer(formatter: Callable):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).set_response_renderer(formatter)
        return fn

    return wrapper


def with_response_additional_headers(headers: dict):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).update_headers(**headers)
        return fn

    return wrapper

from dataclasses import dataclass, field
from typing import Callable, Optional
from typing import List, Dict

from .arguments import Spec, get_unwrapped_function
from .constants import VIEW_ATTR_NAME
from .settings import Settings
from .utils import decorator_with_arguments


@dataclass
class Options:
    spec: Spec = None

    accepted_methods: List[str] = field(default_factory=list)
    response_additional_headers: Dict[str, str] = field(default_factory=dict)
    request_formatter: Optional[Callable] = None
    response_formatter: Optional[Callable] = None
    camelcased_response_data: bool = False
    underscored_request_data: bool = False
    body_arg_name: Optional[str] = None

    def __post_init__(self):
        settings = Settings()

        if settings.response_additional_headers is not None:
            self.response_additional_headers = settings.response_additional_headers
        if settings.camelcased_response_data is not None:
            self.camelcased_response_data = settings.camelcased_response_data
        if settings.underscored_request_data is not None:
            self.underscored_request_data = settings.underscored_request_data
        if settings.body_arg_name is not None:
            self.body_arg_name = settings.body_arg_name

    @classmethod
    def get_or_contribute(cls, fn: Callable) -> "Options":
        """ Get or add special attribute to function with class `ViewOptions` instance and return it """
        if hasattr(fn, VIEW_ATTR_NAME):
            options = getattr(fn, VIEW_ATTR_NAME)
        else:
            options = cls()
            setattr(fn, VIEW_ATTR_NAME, options)

        return options

    @classmethod
    def register(cls, fn: Callable, args: Dict[str, any] = None) -> Callable:
        """ Add options to function if not present, parse function signature and add spec to options """
        opts = cls.get_or_contribute(fn)

        if opts.spec is not None:
            raise RuntimeError("Can't create multiple routes for one function")

        opts.spec = Spec.get(fn, arg_types_override=args)

        return fn

    def add_accepted_methods(self, *methods: str):
        methods = set(map(lambda x: str(x).upper(), methods))
        self.accepted_methods += [method for method in methods if method not in self.accepted_methods]

    def update_headers(self, **headers: str):
        self.response_additional_headers.update(headers)

    def set_request_formatter(self, formatter: Callable):
        if not callable(formatter):
            raise ValueError("Formatter %r must be callable" % formatter)
        self.request_formatter = formatter

    def set_response_formatter(self, formatter: Callable):
        if not callable(formatter):
            raise ValueError("Formatter %r must be callable" % formatter)
        self.response_formatter = formatter

    def set_body_arg_name(self, name: str):
        if not isinstance(name, str):
            raise ValueError("Body name must be string")
        self.body_arg_name = name


def _get_or_contribute(fn: Callable):
    return Options.get_or_contribute(get_unwrapped_function(fn))


@decorator_with_arguments
def with_camelcased_response(fn: Callable):
    _get_or_contribute(fn).camelcased_response_data = True
    return fn


@decorator_with_arguments
def with_underscored_request(fn: Callable):
    _get_or_contribute(fn).underscored_request_data = True
    return fn


def with_request_formatter(formatter: Callable):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).set_request_formatter(formatter)
        return fn

    return wrapper


def with_response_formatter(formatter: Callable):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).set_response_formatter(formatter)
        return fn

    return wrapper


def rename_body_arg(name: str):
    def wrapper(fn: Callable):
        _get_or_contribute(fn).set_body_arg_name(name)
        return fn

    return wrapper

from dataclasses import dataclass, field
from typing import Callable
from typing import List, Dict

from django_hug.arguments import get_unwrapped_function
from .arguments import Spec
from .constants import VIEW_ATTR_NAME
from .utils import decorator_with_arguments


@dataclass
class Options:
    spec: Spec = None

    accepted_methods: List[str] = field(default_factory=list)
    response_additional_headers: Dict[str, str] = field(default_factory=dict)
    request_formatter: Callable = None
    response_formatter: Callable = None
    camelcased_response_data: bool = False
    underscored_request_data: bool = False

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


@decorator_with_arguments
def with_camelcased_response(fn: Callable):
    Options.get_or_contribute(get_unwrapped_function(fn)).camelcased_response_data = True
    return fn


@decorator_with_arguments
def with_underscored_request(fn: Callable):
    Options.get_or_contribute(get_unwrapped_function(fn)).underscored_request_data = True
    return fn


def with_request_formatter(formatter: Callable):
    def wrapper(fn: Callable):
        Options.get_or_contribute(get_unwrapped_function(fn)).set_request_formatter(formatter)
        return fn

    return wrapper


def with_response_formatter(formatter: Callable):
    def wrapper(fn: Callable):
        Options.get_or_contribute(get_unwrapped_function(fn)).set_response_formatter(formatter)
        return fn

    return wrapper

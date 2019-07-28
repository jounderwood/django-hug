from dataclasses import dataclass, field
from typing import List, Callable, Dict

from djhug.arguments import Spec
from djhug.constants import VIEW_ATTR_NAME
from djhug.format import is_valid_request_formatter, is_valid_response_formatter


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
            raise RuntimeError("Can't register multiple routes for one function")

        opts.spec = Spec.get(fn, arg_types_override=args)

        return fn

    def add_accepted_methods(self, *methods: str):
        methods = set(map(lambda x: str(x).upper(), methods))
        self.accepted_methods += [method for method in methods if method not in self.accepted_methods]

    def update_headers(self, **headers: str):
        self.response_additional_headers.update(headers)

    def set_request_formatter(self, formatter: Callable):
        if not is_valid_request_formatter(formatter):
            raise ValueError(
                "Formatter %r is invalid, formatter must be function decorated with "
                "`djhug.formatter` decorator" % formatter
            )
        self.request_formatter = formatter

    def set_response_formatter(self, formatter: Callable):
        if not is_valid_response_formatter(formatter):
            raise ValueError(
                "Formatter %r is invalid, formatter must be function decorated with "
                "`djhug.formatter` decorator" % formatter
            )
        self.response_formatter = formatter

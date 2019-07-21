from dataclasses import dataclass, field
from typing import List, Callable, Dict

from djhug.arguments import Spec
from djhug.constants import VIEW_ATTR_NAME


@dataclass
class Options:
    spec: Spec = None

    accepted_methods: List[str] = field(default_factory=list)
    response_additional_headers: Dict[str, str] = field(default_factory=dict)
    request_converters: List[Callable] = field(default_factory=list)
    response_converters: List[Callable] = field(default_factory=list)

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
        _hash = hash(fn)

        if opts.spec is not None:
            raise RuntimeError("Can't register multiple routes for one function")

        opts.spec = Spec.get(fn, arg_types_override=args)
        opts._hash = hash(fn)

        return fn

    def add_accepted_methods(self, *methods: str):
        methods = set(map(lambda x: str(x).upper(), methods))
        self.accepted_methods += [method for method in methods if method not in self.accepted_methods]

    def update_headers(self, **headers: str):
        self.response_additional_headers.update(headers)

    def add_request_converters(self, *converters: List[Callable]):
        self.request_converters += self._clean_converters(self.request_converters, converters)

    def add_response_converters(self, *converters):
        self.response_converters += self._clean_converters(self.response_converters, converters)

    @staticmethod
    def _clean_converters(current_converters, converters):
        return [converter for converter in set(converters) if converter not in current_converters]

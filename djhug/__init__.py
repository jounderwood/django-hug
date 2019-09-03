from .formatters import request_parser, response_formatter
from .options import (
    with_request_parser,
    with_response_formatter,
    with_camelcased_response,
    with_underscored_request,
    rename_body_arg,
)
from .routes import Routes, route

__all__ = ("route", "Routes", "request", "request_parser", "response", "response_formatter", "rename_body_arg")


class _Request:
    format = staticmethod(with_request_parser)
    underscored = staticmethod(with_underscored_request)

    register_parser = staticmethod(request_parser)


class _Response:
    format = staticmethod(with_response_formatter)
    camelcased = staticmethod(with_camelcased_response)

    register_formatter = staticmethod(response_formatter)


request = _Request()
response = _Response()

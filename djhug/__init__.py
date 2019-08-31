from .options import (
    with_request_formatter,
    with_response_formatter,
    with_camelcased_response,
    with_underscored_request,
)
from .formatters import request_formatter, response_formatter
from .routes import Routes, route

__all__ = ("route", "Routes", "request", "request_formatter", "response", "response_formatter")


class _Request:
    format = staticmethod(with_request_formatter)
    underscored = staticmethod(with_underscored_request)

    register_formatter = staticmethod(request_formatter)


class _Response:
    format = staticmethod(with_response_formatter)
    camelcased = staticmethod(with_camelcased_response)

    register_formatter = staticmethod(response_formatter)


request = _Request()
response = _Response()

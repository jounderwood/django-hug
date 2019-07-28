from .decorators import (
    route,
    with_request_format,
    with_response_format,
    with_camelcased_response,
    with_underscored_request,
)
from .format import request_formatter, response_formatter
from .routes import Routes

__all__ = ("route", "Routes", "response", "request")


class _Request:
    format = staticmethod(with_request_format)
    underscored = staticmethod(with_underscored_request)

    register_formatter = staticmethod(request_formatter)


class _Response:
    format = staticmethod(with_response_format)
    camelcased = staticmethod(with_camelcased_response)

    register_formatter = staticmethod(response_formatter)


request = _Request()
response = _Response()

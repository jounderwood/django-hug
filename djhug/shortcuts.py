from .content_negotiation import request_parser, response_renderer
from .options import (
    with_request_parser,
    with_response_renderer,
    with_response_additional_headers,
    with_camelcased_response_data,
    with_underscored_body_data,
)


class _Request:
    parser = staticmethod(with_request_parser)
    underscored_body = staticmethod(with_underscored_body_data)
    register_parser = staticmethod(request_parser)


class _Response:
    renderer = staticmethod(with_response_renderer)
    camelcased = staticmethod(with_camelcased_response_data)
    add_headers = staticmethod(with_response_additional_headers)

    register_renderer = staticmethod(response_renderer)


request = _Request()
response = _Response()

from collections import Callable

import pytest

from djhug import request_parser, response_renderer
from djhug.constants import REQUEST_PARSER_ATTR_NAME, RESPONSE_RENDERER_ATTR_NAME
from djhug.content_negotiation import (
    get_request_parsers,
    get_response_renderers,
)


@pytest.mark.parametrize(
    "decorator, get_function, attr_name",
    (
        (request_parser, get_request_parsers, REQUEST_PARSER_ATTR_NAME),
        (response_renderer, get_response_renderers, RESPONSE_RENDERER_ATTR_NAME),
    ),
)
def test_formatter_decorator(decorator: Callable, get_function: Callable, attr_name: str):

    @decorator("application/json")
    def fn_1(data):
        return data

    @decorator(content_type=[])
    def fn_2(data):
        return data

    @decorator(content_type=("application/msgpack", "application/x-msgpack"))
    def fn_3(data):
        return data

    @decorator(["application/bson", "application/vnd.bson"])
    def fn_4(data):
        return data

    for fn in (fn_1, fn_2, fn_3, fn_4):
        assert hasattr(fn, attr_name)

    formatters = get_function()

    assert formatters["application/json"] == fn_1
    assert formatters["application/msgpack"] == fn_3
    assert formatters["application/x-msgpack"] == fn_3
    assert formatters["application/bson"] == fn_4
    assert formatters["application/vnd.bson"] == fn_4

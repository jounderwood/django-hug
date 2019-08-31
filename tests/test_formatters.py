from collections import Callable

import pytest

from djhug import request_formatter, response_formatter
from djhug.constants import REQUEST_FORMATTER_ATTR_NAME, RESPONSE_FORMATTER_ATTR_NAME
from djhug.formatters import (
    get_request_formatters,
    get_response_formatters,
    is_valid_request_formatter,
    is_valid_response_formatter,
)


@pytest.mark.parametrize(
    "decorator, get_function, is_valid, attr_name",
    (
        (request_formatter, get_request_formatters, is_valid_request_formatter, REQUEST_FORMATTER_ATTR_NAME),
        (response_formatter, get_response_formatters, is_valid_response_formatter, RESPONSE_FORMATTER_ATTR_NAME),
    ),
)
def test_formatter_decorator(decorator, get_function, is_valid, attr_name):
    decorator: Callable
    get_function: Callable
    is_valid: Callable
    attr_name: str

    @decorator("application/json")
    def fn_1(data):
        return data

    @decorator(mime_type=[])
    def fn_2(data):
        return data

    @decorator(mime_type=("application/msgpack", "application/x-msgpack"))
    def fn_3(data):
        return data

    @decorator(["application/bson", "application/vnd.bson"])
    def fn_4(data):
        return data

    for fn in (fn_1, fn_2, fn_3, fn_4):
        assert is_valid(fn)
        assert hasattr(fn, attr_name)

    formatters = get_function()

    assert formatters["application/json"] == fn_1
    assert formatters["application/msgpack"] == fn_3
    assert formatters["application/x-msgpack"] == fn_3
    assert formatters["application/bson"] == fn_4
    assert formatters["application/vnd.bson"] == fn_4

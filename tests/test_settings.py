from django.test import override_settings

from djhug import request_parser, response_formatter
from djhug.formatters import get_request_parsers, get_response_formatters
from djhug.settings import Settings


@request_parser("application/x-test")
def request_formatter_test(request):
    return request.POST


@response_formatter("application/x-test")
def response_formatter_test(data):
    return data


def test_register_request_formatters_ok():
    assert Settings().request_formatters is None

    with override_settings(DJHUG_REQUEST_FORMATTERS=["tests.test_settings.request_formatter_test"]):
        assert Settings().request_formatters == ["tests.test_settings.request_formatter_test"]

        assert "application/x-test" in get_request_parsers()
        assert get_request_parsers()["application/x-test"] == request_formatter_test


def test_register_response_formatters_ok():
    assert Settings().response_formatters is None

    with override_settings(DJHUG_RESPONSE_FORMATTERS=["tests.test_settings.response_formatter_test"]):
        assert Settings().response_formatters == ["tests.test_settings.response_formatter_test"]

        assert "application/x-test" in get_response_formatters()
        assert get_response_formatters()["application/x-test"] == response_formatter_test


def test_response_additional_headers_ok():
    assert Settings().response_additional_headers == {}

    with override_settings(DJHUG_RESPONSE_ADDITIONAL_HEADERS={"Access-Control-Allow-Origin": "*"}):
        assert Settings().response_additional_headers == {"Access-Control-Allow-Origin": "*"}


def test_camelcased_response_data_ok():
    assert not Settings().camelcased_response_data

    with override_settings(DJHUG_CAMELCASED_RESPONSE_DATA=True):
        assert Settings().camelcased_response_data


def test_underscored_request_data_ok():
    assert not Settings().underscored_request_data

    with override_settings(DJHUG_UNDERSCORED_REQUEST_DATA=True):
        assert Settings().underscored_request_data

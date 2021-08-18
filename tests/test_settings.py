from django.test import override_settings

from djhug import request_parser, response_renderer
from djhug.content_negotiation import get_request_parsers, get_response_renderers
from djhug.settings import Settings


@request_parser("application/x-test")
def request_formatter_test(request):
    return request.POST


@response_renderer("application/x-test")
def response_formatter_test(data):
    return data


def test_register_request_formatters_ok():
    assert Settings().request_parsers_modules is None

    with override_settings(DJHUG_REQUEST_PARSERS_MODULES=["tests.test_settings"]):
        assert Settings().request_parsers_modules == ["tests.test_settings"]

        assert "application/x-test" in get_request_parsers()
        assert get_request_parsers()["application/x-test"] == request_formatter_test


def test_register_response_formatters_ok():
    assert Settings().response_renderers_modules is None

    with override_settings(DJHUG_RESPONSE_RENDERERS_MODULES=["tests.test_settings"]):
        assert Settings().response_renderers_modules == ["tests.test_settings"]

        assert "application/x-test" in get_response_renderers()
        assert get_response_renderers()["application/x-test"] == response_formatter_test


def test_response_additional_headers_ok():
    assert Settings().response_additional_headers == {}

    with override_settings(DJHUG_RESPONSE_ADDITIONAL_HEADERS={"Access-Control-Allow-Origin": "*"}):
        assert Settings().response_additional_headers == {"Access-Control-Allow-Origin": "*"}


def test_camelcased_response_data_ok():
    assert not Settings().camelcased_response_data

    with override_settings(DJHUG_CAMELCASED_RESPONSE_DATA=True):
        assert Settings().camelcased_response_data
    del Settings()._Settings__shared_state['camelcased_response_data']

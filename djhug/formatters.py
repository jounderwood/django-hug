import json
from typing import Callable, Dict, Union, List, Optional

from django.core.serializers.json import DjangoJSONEncoder

from djhug.constants import REQUEST_PARSER_ATTR_NAME, RESPONSE_FORMATTER_ATTR_NAME, ContentTypes

_global_request_parsers = {}
_global_response_formatters = {}


def _register_formatter(
    callback: Callable, content_type: Optional[Union[str, List[str]]], storage: dict, attr_name: str
):
    setattr(callback, attr_name, True)

    if content_type is not None and not isinstance(content_type, (str, list, tuple)):
        raise ValueError("Mime type must be string or tuple")

    content_type = content_type or "*"

    if isinstance(content_type, str):
        content_type = [content_type]

    for mt in content_type:
        storage[mt] = callback

    return callback


def request_parser(content_type: Optional[Union[str, List[str]]] = None):
    def wrap(fn: Callable):
        _register_formatter(
            fn, content_type=content_type, storage=_global_request_parsers, attr_name=REQUEST_PARSER_ATTR_NAME
        )
        return fn

    return wrap


def response_formatter(content_type: Optional[Union[str, List[str]]] = None):
    def wrap(fn: Callable):
        _register_formatter(
            fn, content_type=content_type, storage=_global_response_formatters, attr_name=RESPONSE_FORMATTER_ATTR_NAME
        )
        return fn

    return wrap


def is_valid_request_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, REQUEST_PARSER_ATTR_NAME)


def is_valid_response_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, RESPONSE_FORMATTER_ATTR_NAME)


def get_request_parsers() -> Dict[str, Callable]:
    return _global_request_parsers


def get_request_parser(content_type: str) -> Optional[Callable]:
    parsers = get_request_parsers()

    return parsers.get(content_type, parsers.get("*"))


def get_response_formatters() -> Dict[str, Callable]:
    return _global_response_formatters


def get_response_formatter(content_type: str) -> Optional[Callable]:
    formatters = get_response_formatters()

    return formatters.get(content_type, formatters.get("*"))


@request_parser((ContentTypes.FORM, ContentTypes.FORM_URLENCODED))
def multipart_request(request):
    return request.POST


@request_parser(("*", ContentTypes.JSON))
def json_request(request):
    return json.loads(request.body.decode(request.encoding or "utf-8"))


@response_formatter(("*", ContentTypes.JSON))
def json_response(response_data) -> str:
    return json.dumps(response_data, cls=DjangoJSONEncoder)

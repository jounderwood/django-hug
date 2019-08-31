import json
from typing import Callable, Dict, Union, List

from django.core.serializers.json import DjangoJSONEncoder

from djhug.constants import REQUEST_FORMATTER_ATTR_NAME, RESPONSE_FORMATTER_ATTR_NAME

_global_request_formatters = {}
_global_response_formatters = {}


def _register_formatter(callback: Callable, mime_type: Union[str, List[str]], storage: dict, attr_name: str):
    setattr(callback, attr_name, True)

    if not isinstance(mime_type, (str, list, tuple)):
        raise ValueError("Mime type must be string or tuple")

    if isinstance(mime_type, str):
        mime_type = [mime_type]

    for mt in mime_type:
        storage[mt] = callback

    return callback


def request_formatter(mime_type: Union[str, List[str]]):
    def wrap(fn: Callable):
        _register_formatter(
            fn, mime_type=mime_type, storage=_global_request_formatters, attr_name=REQUEST_FORMATTER_ATTR_NAME
        )
        return fn

    return wrap


def response_formatter(mime_type: Union[str, List[str]]):
    def wrap(fn: Callable):
        _register_formatter(
            fn, mime_type=mime_type, storage=_global_response_formatters, attr_name=RESPONSE_FORMATTER_ATTR_NAME
        )
        return fn

    return wrap


def is_valid_request_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, REQUEST_FORMATTER_ATTR_NAME)


def is_valid_response_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, RESPONSE_FORMATTER_ATTR_NAME)


def get_request_formatters() -> Dict[str, Callable]:
    return _global_request_formatters


def get_response_formatters() -> Dict[str, Callable]:
    return _global_response_formatters


@request_formatter("application/json")
def json_request(request):
    return json.loads(request.body.decode(request.encoding or "utf-8"))


@response_formatter("application/json")
def json_response(response_data) -> str:
    return json.dumps(response_data, cls=DjangoJSONEncoder)

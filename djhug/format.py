from functools import partial
from typing import Callable, Optional, Dict, Union, List

from djhug.constants import REQUEST_FORMATTER_ATTR_NAME, RESPONSE_FORMATTER_ATTR_NAME
from .utils import decorator_with_arguments

_global_request_formatters = {}
_global_response_formatters = {}


def _formatter(
    callback: Callable,
    mime_type: Optional[Union[str, List[str]]] = None,
    storage: Optional[dict] = None,
    attr_name: str = REQUEST_FORMATTER_ATTR_NAME,
):
    setattr(callback, attr_name, True)

    if isinstance(mime_type, str):
        mime_type = [mime_type]
    if mime_type is None:
        mime_type = []

    for mt in mime_type:
        if mt is not None:
            storage[mt] = callback

    return callback


request_formatter = decorator_with_arguments(
    partial(_formatter, storage=_global_request_formatters, attr_name=REQUEST_FORMATTER_ATTR_NAME)
)
response_formatter = decorator_with_arguments(
    partial(_formatter, storage=_global_response_formatters, attr_name=RESPONSE_FORMATTER_ATTR_NAME)
)


def is_valid_request_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, REQUEST_FORMATTER_ATTR_NAME)


def is_valid_response_formatter(formatter: Callable) -> bool:
    return callable(formatter) and hasattr(formatter, RESPONSE_FORMATTER_ATTR_NAME)


def get_request_formatters() -> Dict[str, Callable]:
    return _global_request_formatters


def get_response_formatters() -> Dict[str, Callable]:
    return _global_response_formatters

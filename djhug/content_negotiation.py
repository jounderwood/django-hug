import cgi
import json
from typing import Callable, Dict, Union, Optional, Iterable

from django.core.serializers.json import DjangoJSONEncoder
from django.http.request import HttpRequest

from djhug.constants import REQUEST_PARSER_ATTR_NAME, RESPONSE_RENDERER_ATTR_NAME, ContentType

_global_request_parsers: Dict[str, Callable] = {}
_global_response_formatters: Dict[str, Callable] = {}


def request_parser(content_type: Union[str, Iterable[str]]):
    def wrap(fn: Callable):
        _register(fn, media_type=content_type, storage=_global_request_parsers, attr_name=REQUEST_PARSER_ATTR_NAME)
        return fn

    return wrap


def response_renderer(content_type: Union[str, Iterable[str]]):
    def wrap(fn: Callable):
        _register(
            fn, media_type=content_type, storage=_global_response_formatters, attr_name=RESPONSE_RENDERER_ATTR_NAME
        )
        return fn

    return wrap


def _register(callback: Callable, media_type: Optional[Union[str, Iterable[str]]], storage: dict, attr_name: str):
    setattr(callback, attr_name, media_type)

    if media_type is not None and not isinstance(media_type, (str, list, tuple)):
        raise ValueError("Media type must be string or tuple")

    media_type = media_type or "*"

    if isinstance(media_type, str):
        media_type = [media_type]

    for mt in media_type:
        storage[mt] = callback

    return callback


def get_request_parsers() -> Dict[str, Callable]:
    return _global_request_parsers


def get_response_renderers() -> Dict[str, Callable]:
    return _global_response_formatters


def get_request_parser(request: HttpRequest) -> Callable:
    parsers = get_request_parsers()

    return parsers.get(request.content_type)


def get_response_renderer(request: HttpRequest) -> Optional[Callable]:
    meta = request.META
    content_type, _ = cgi.parse_header(meta.get("HTTP_ACCEPT", meta.get("Accept")) or "")
    content_type = content_type.split(",")[0]

    renderers = get_response_renderers()

    return renderers.get(content_type) or json_renderer


def get_renderer_content_type(renderer: Callable):
    return getattr(renderer, RESPONSE_RENDERER_ATTR_NAME, None)


@request_parser((ContentType.FORM, ContentType.FORM_URLENCODED))
def form_parser(request):
    return request.POST.dict()


@request_parser(ContentType.JSON)
def json_parser(request):
    return json.loads(request.body.decode(request.encoding or "utf-8"))


@response_renderer(ContentType.JSON)
def json_renderer(response_data) -> str:
    return json.dumps(response_data, cls=DjangoJSONEncoder)


@response_renderer(ContentType.TEXT)
def plain_renderer(response_data) -> str:
    return str(response_data)


@response_renderer(ContentType.HTML)
def html_renderer(response_data) -> str:
    return str(response_data)

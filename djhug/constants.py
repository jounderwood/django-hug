import inspect

EMPTY = inspect.Signature.empty


class HTTP:
    CONNECT = "CONNECT"
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"

    ALL = (CONNECT, DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, TRACE)
    WITH_BODY = (POST, PUT, PATCH)


class ContentType:
    HTML = "text/html"
    TEXT = "text/plain"
    JSON = "application/json"
    FORM = "multipart/form-data"
    FORM_URLENCODED = "application/x-www-form-urlencoded"


VIEW_ATTR_NAME = "__djhug_options__"
DIRECTIVE_ATTR_NAME = "__djhug_directive__"
REQUEST_PARSER_ATTR_NAME = "__djhug_request_parser__"
RESPONSE_RENDERER_ATTR_NAME = "__djhug_response_renderer__"

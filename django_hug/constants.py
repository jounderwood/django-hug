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


class ContentTypes:
    HTML = "text/html"
    TEXT = "text/plain"
    JSON = "application/json"
    FORM = "multipart/form-data"
    FORM_URLENCODED = "application/x-www-form-urlencoded"


class JsonStyleFormat:
    CAMELCASE = "camelcase"
    UNDERSCORE = "underscore"

    ALL = (CAMELCASE, UNDERSCORE)

class Error(Exception):
    pass


class RequestError(Error):
    pass


class HttpResponseError(Error):
    status = 400


class HttpNotAllowed(HttpResponseError):
    status = 405

import json
from typing import Union


class DjhugError(Exception):
    pass


class RequestError(DjhugError):
    pass


class ValidationError(ValueError, RequestError):
    def __init__(self, data: Union[str, dict, Exception]):
        msg = ''
        if isinstance(data, dict):
            try:
                self.error_data = data
                msg = json.dumps(data)
            except (ValueError, TypeError):
                self.error_data = None
        elif isinstance(data, Exception):
            msg = str(data)

        super().__init__(self, msg)


class HttpResponseError(DjhugError):
    status = 400


class HttpNotAllowed(HttpResponseError):
    status = 405


class HttpValidationError(ValidationError, HttpResponseError):
    status = 400

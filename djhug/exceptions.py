from typing import Union, List, Dict, Optional

from django.core.exceptions import ImproperlyConfigured


class DjhugError(Exception):
    pass


class ConfigError(ImproperlyConfigured, DjhugError):
    pass


class RequestError(DjhugError):
    pass


class ValidationError(RequestError):
    def __init__(self, errors: Union[str, Dict[str, List[Union[dict, str]]]]):
        if isinstance(errors, dict):
            self.errors = errors
            self.msg = "Validation error"
        else:
            self.msg = errors
            self.errors = {}
        super().__init__(self.msg)


class HttpBadRequest(DjhugError):
    status = 400


class HttpNotAllowed(HttpBadRequest):
    status = 405


class HttpNotAcceptable(HttpBadRequest):
    status = 406

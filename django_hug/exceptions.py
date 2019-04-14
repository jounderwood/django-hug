from typing import Dict

from marshmallow import ValidationError as MarshmallowValidationError


class Error(Exception):
    pass


class RequestError(Error):
    pass


class ValidationError(ValueError, RequestError):
    def __init__(self, message=None, **fields_errors: Dict[str, str]):
        if message:
            fields_errors[""] = message

        self.message = message
        self.fields_errors = fields_errors
        super().__init__(self, str(fields_errors))

    @classmethod
    def from_marshmallow_error(cls, e: MarshmallowValidationError):
        return cls(**e.normalized_messages())


class HttpResponseError(Error):
    status = 400


class HttpNotAllowed(HttpResponseError):
    status = 405


class HttpValidationError(ValidationError, HttpResponseError):
    status = 400

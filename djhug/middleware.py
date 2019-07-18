import logging
from collections import Mapping
from typing import Callable, Iterable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class DjhugMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        pass

    def process_view(self, request: HttpRequest, view_func: Callable, view_args: Iterable, view_kwargs: Mapping):
        return request

    def process_response(self, request: HttpRequest, response: HttpResponse):
        return response

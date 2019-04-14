import json
from typing import Callable

from django_hug.constants import ContentTypes

_registered_directives = {}


def directive(fn: Callable):
    if not callable(fn):
        raise ValueError("Directive must be callable")

    _registered_directives[fn.__name__] = fn
    fn._django_hug_directive = True

    return fn


def get_directive(fn):
    return _registered_directives.get(fn)


def get_available_directives():
    return _registered_directives


@directive
def body(request):
    content_type = request.content_type.lower()
    if ContentTypes.FORM_URLENCODED in content_type or ContentTypes.FORM in content_type:
        return request.POST
    else:
        return json.loads(request.body.decode(request.encoding or "utf-8"))

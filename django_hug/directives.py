import json

_available_directives = {}


def directive(fn):
    _available_directives[fn.__name__] = fn
    fn._directive = True
    return fn


def get_directive(fn):
    return _available_directives[fn]


def get_available_directives():
    return _available_directives


@directive
def body(request):
    if "multipart/form-data" in request.content_type.lower():
        return request.POST
    else:
        return json.loads(request.body.decode("utf-8"))

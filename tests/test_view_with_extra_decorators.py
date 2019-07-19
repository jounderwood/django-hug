import json
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from marshmallow import fields

from djhug.arguments import Spec
from djhug.routes import route, ViewOptions, Routes

routes = Routes()


def update_kwargs(fn):
    @wraps(fn)
    def wrap(*args, **kwargs):
        return fn(*args, from_decorator=1, **kwargs)

    return wrap


def update_kwargs_no_wrap(fn):
    def wrap(*args, **kwargs):
        return fn(*args, no_wrap_decorator=1, **kwargs)

    return wrap


def _get_locals_response(locals):
    locals.pop("request", None)
    return JsonResponse(locals)


@routes.get("view_update_kwargs/")
@update_kwargs
@require_GET
def view_update_kwargs(request, year: int = 1, **kwargs):
    return _get_locals_response(locals())


@require_GET
@update_kwargs
@routes.get("view_update_kwargs_2/")
def view_update_kwargs_2(request, year: int = 1, **kwargs):
    return _get_locals_response(locals())


@update_kwargs
@routes.get("view_update_kwargs_3/")
@require_GET
def view_update_kwargs_2(request, year: int = 1, **kwargs):
    return _get_locals_response(locals())


def test_wrapped_decorators_ok(client, with_urlpatterns):
    with_urlpatterns(routes.get_urlpatterns())

    for url in ("/view_update_kwargs/", "/view_update_kwargs_2/", "/view_update_kwargs_3/"):
        resp: HttpResponse = client.get(url)
        assert resp.status_code == 200, resp.content
        assert json.loads(resp.content) == {"year": 1, "kwargs": {"from_decorator": 1}}

        resp: HttpResponse = client.post(url)
        assert resp.status_code == 405, resp.content

    assert "year" in view_update_kwargs.__djhug_options__.spec.arg_types_map


# def test_decorators_closured_view_ok(client, with_urlpatterns, routes: Routes):
#     @routes.get("api/(?P<year>[0-9]{4})/", re=True)
#     def view(request, year: int):
#         loc = locals()
#         del loc["request"]
#         return JsonResponse(loc)
#
#     with_urlpatterns(routes.get_urlpatterns())
#     resp: HttpResponse = client.get("/api/0001/")
#
#     assert resp.status_code == 200, resp.content
#     assert json.loads(resp.content) == {"year": "0001"}

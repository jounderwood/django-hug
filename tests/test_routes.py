import json
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from marshmallow import fields

from djhug.arguments import Spec
from djhug.routes import route, ViewOptions, Routes


def test_options_contribute():
    @route
    def view(request, year: int, name: str, q1: float = 0, q2: str = "firefire") -> dict:
        return locals()

    opts = view.__djhug_options__
    assert isinstance(opts, ViewOptions)
    assert isinstance(opts.spec, Spec)
    assert [arg.name for arg in opts.spec.args] == ["request", "year", "name", "q1", "q2"]


def test_options_contribute_decorator_call():
    @route(uuu=1)
    def view(a=1) -> dict:
        return locals()

    assert isinstance(view.__djhug_options__, ViewOptions)


def test_route_args_override():
    @route(args={"a": fields.Int()})
    def view(a: int = 1) -> dict:
        return locals()

    assert isinstance(view.__djhug_options__.spec.arg_types_map["a"], fields.Int)


def test_register_django_simple_url(client, with_urlpatterns, routes: Routes):
    @routes.get("<int:year>/<str:name>/")
    def view(request, year: int, name: str):
        loc = locals()
        del loc["request"]
        return JsonResponse(loc)

    with_urlpatterns(routes.get_urlpatterns())
    resp: HttpResponse = client.get("/123/foo/")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 123, "name": "foo"}


def test_register_django_regex_url(client, with_urlpatterns, routes: Routes):
    @routes.get("api/(?P<year>[0-9]{4})/", re=True)
    def view(request, year: int):
        loc = locals()
        del loc["request"]
        return JsonResponse(loc)

    with_urlpatterns(routes.get_urlpatterns())
    resp: HttpResponse = client.get("/api/0001/")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": "0001"}


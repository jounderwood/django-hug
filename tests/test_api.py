import json
from functools import wraps

import pytest
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from marshmallow import Schema, fields

import django_hug


def test_simple_get_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("<int:year>/<str:name>/")
    def view(request, year: int, name: str, q1: float = 0, q2: str = "firefire"):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/123/alarm/?q1=23.2000&wat=meh")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 123, "name": "alarm", "q1": 23.2, "q2": "firefire"}


def test_simple_get_regex_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("(?P<year>[0-9]{4})/", re=True)
    def view(request, year: int, name: str):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/000/")

    assert resp.status_code == 404, resp.content

    resp: HttpResponse = client.get("/1911/?name=ouch")
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 1911, "name": "ouch"}


def test_simple_post_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.post("<str:name>/")
    def view(request, name: str, product_id: int, quantity: int, q: str = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/purchase/?q=param", data={"product_id": 999, "quantity": 20})

    assert resp.status_code == 201, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "q": "param", "product_id": 999, "quantity": 20}


def test_marshmallow_whole_body_post_ok(client, with_urlpatterns, routes: django_hug.Routes):
    class RespSchema(Schema):
        product_id = fields.Int(required=True)
        quantity = fields.Int(required=True)

    @routes.post("<str:name>/")
    def view(request, name: str, body: RespSchema()):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123})

    assert resp.status_code == 400, resp.content

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123, "quantity": 3})
    assert resp.status_code == 201, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "body": {"product_id": 123, "quantity": 3}}


def test_custom_headers(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("test/", response_headers={"X-Accel-Expires": 20, "content-type": "text/html"})
    def view(request, name: str = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/", data={"name": "gizmo"})

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "gizmo"}

    assert resp["Content-Type"] == "text/html"
    assert resp["X-Accel-Expires"] == "20"


@pytest.mark.skip("Not supported yet")
def test_multiple_routes(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.post("post/")
    @routes.get("get_patch/<str:name>/")
    @routes.patch("get_patch/<str:name>/")
    def strange_view(request, name: str = None, number: int = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/post/", data={"name": None, "number": "11"})
    assert resp.status_code == 201, resp.content
    assert json.loads(resp.content) == {"number": 11}

    resp: HttpResponse = client.get("/get_patch/wow/", data={"number": 5})
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "wow", "number": 11}

    resp: HttpResponse = client.patch("/get_patch/wow/")
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "wow", "number": None}


def test_simple_validation_errors_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("test/")
    def view(request, year: int, month: int = 1, day: int = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?month=unknown&day=1")

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {"year": ["Missing data for required field."], "month": ["Not a valid integer."]}
    }


def test_marshmallow_validation_errors_ok(client, with_urlpatterns, routes: django_hug.Routes):
    class RespSchema(Schema):
        id = fields.Int(required=True)
        quantity = fields.Int(required=True)

    @routes.post("test/")
    def view(request, body: RespSchema(), q1: int, q2: int, q3: fields.Int()):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/test/?q2=1&q3=aaa", data={"id": 123})

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {
            "quantity": ["Missing data for required field."],
            "q1": ["Missing data for required field."],
            "q3": ["Not a valid integer."],
        }
    }


@pytest.mark.skip("Not supported yet")
def test_decorators(client, with_urlpatterns, routes: django_hug.Routes):
    def decorator(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            return fn(*args, from_decorator=1, **kwargs)

        return wrap

    def decorator_no_wrap(fn):
        def wrap(*args, **kwargs):
            return fn(*args, no_wrap_decorator=1, **kwargs)

        return wrap

    @decorator_no_wrap
    @require_GET
    @decorator
    @routes.get("test/")
    def view(request, name: str, from_decorator=None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?name=aaa")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "aaa", "from_decorator": 1, "no_wrap_decorator": 1}


@pytest.mark.parametrize("path", ("test/", "/test/"))
@pytest.mark.parametrize("prefix", ("api", "/api", "api/", "/api/"))
def test_routes_prefix(client, with_urlpatterns, prefix, path):
    routes = django_hug.Routes(prefix=prefix)

    @routes.get(path)
    def view(request, name: str = None):
        return {}

    with_urlpatterns(routes.get_urlpatterns())
    assert client.get("/api/test/").status_code == 200


def test_no_annotation(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("test/")
    def view(request, year, day: int = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?day=1")

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {"year": ["Missing data for required field."]}
    }

    resp: HttpResponse = client.get("/test/?day=1&year=111")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"day": 1, "year": "111"}

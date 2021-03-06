import json

import pytest
from django.http import HttpResponse
from pydantic import PositiveFloat

import djhug
from djhug.arguments import Body


def test_simple_get_ok(client, with_urlpatterns, routes: djhug.Routes):
    @routes.get("<int:year>/<str:name>/")
    def view(request, year: int, name: str, q1: float = 0, q2: str = "firefire"):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/123/alarm/?q1=23.2000&wat=meh")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 123, "name": "alarm", "q1": 23.2, "q2": "firefire"}


def test_simple_get_regex_ok(client, with_urlpatterns, routes: djhug.Routes):
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


def test_simple_post_ok(client, with_urlpatterns, routes: djhug.Routes):
    @routes.post("<str:name>/")
    def view(request, name: str, product_id: int, quantity: int, q: str = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/purchase/?q=param", data={"product_id": 999, "quantity": 20})

    assert resp.status_code == 201, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "q": "param", "product_id": 999, "quantity": 20}


def test_whole_body_post_ok(client, with_urlpatterns, routes: djhug.Routes):
    class RespModel(Body):
        product_id: int
        quantity: int

    @routes.post("<str:name>/")
    def view(request, name: str, body: RespModel):
        return {"name": name, "body": body.dict()}

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123})

    assert resp.status_code == 400, resp.content

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123, "quantity": 3})
    assert resp.status_code == 201, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "body": {"product_id": 123, "quantity": 3}}


def test_custom_headers(client, with_urlpatterns, routes: djhug.Routes):
    @djhug.response.add_headers({"X-Accel-Expires": 20, "content-type": "text/html"})
    @routes.get("test/")
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


def test_simple_validation_errors_ok(client, with_urlpatterns, routes: djhug.Routes):
    @routes.get("test/")
    def view(request, year: int, month: int = 1, day: int = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?month=unknown&day=1")

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {
            "month": [{"loc": ["__root__"], "msg": "value is not a valid integer", "type": "type_error.integer"}],
            "year": [{"loc": ["year"], "msg": "field required", "type": "value_error.missing"}],
        }
    }


def test_with_body_model_validation_errors_ok(client, with_urlpatterns, routes: djhug.Routes):
    class RespBody(Body):
        id: int
        quantity: int

    @routes.post("test/")
    def view(request, body: RespBody, q1: int, q2: int, q3: PositiveFloat):
        return {}

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.post("/test/?q2=1&q3=aaa", data={"id": 123})

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {
            "body": [{"loc": ["quantity"], "msg": "field required", "type": "value_error.missing"}],
            "q1": [{"loc": ["q1"], "msg": "field required", "type": "value_error.missing"}],
            "q3": [{"loc": ["__root__"], "msg": "value is not a valid float", "type": "type_error.float"}],
        }
    }


@pytest.mark.parametrize("path", ("test/", "/test/"))
@pytest.mark.parametrize("prefix", ("api", "/api", "api/", "/api/"))
def test_routes_prefix(client, with_urlpatterns, prefix, path):
    routes = djhug.Routes(prefix=prefix)

    @routes.get(path)
    def view(request, name: str = None):
        return {}

    with_urlpatterns(routes.get_urlpatterns())
    assert client.get("/api/test/").status_code == 200


def test_no_annotation(client, with_urlpatterns, routes: djhug.Routes):
    @routes.get("test/")
    def view(request, year, day: int = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?day=1")

    assert resp.status_code == 400, resp.content
    assert json.loads(resp.content) == {
        "errors": {"year": [{"loc": ["year"], "msg": "field required", "type": "value_error.missing"}]}
    }

    resp: HttpResponse = client.get("/test/?day=1&year=111")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"day": 1, "year": "111"}


def test_args_kwargs_ok(client, with_urlpatterns, routes: djhug.Routes):
    @routes.get("test/")
    def view(request, name, *args, **kwargs):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.get_urlpatterns()))

    resp: HttpResponse = client.get("/test/?name=John")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "John", "args": [], "kwargs": {}}

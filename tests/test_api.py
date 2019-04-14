import json

from django.http import HttpResponse
from marshmallow import Schema, fields

import django_hug


def test_simple_get_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("<int:year>/<str:name>/")
    def fn(request, year: int, name: str, q1: float = 0, q2: str = "firefire"):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.urls()))

    resp: HttpResponse = client.get("/911/alarm/?q1=23.2000&wat=meh")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 911, "name": "alarm", "q1": 23.2, "q2": "firefire"}


def test_simple_get_regex_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.get("(?P<year>[0-9]{4})/", re=True)
    def fn(request, year: int, name: str):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.urls()))

    resp: HttpResponse = client.get("/911/")

    assert resp.status_code == 404, resp.content

    resp: HttpResponse = client.get("/1911/?name=ouch")
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 1911, "name": "ouch"}


def test_simple_post_ok(client, with_urlpatterns, routes: django_hug.Routes):
    @routes.post("<str:name>/")
    def fn(request, name: str, product_id: int, quantity: int, q: str = None):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.urls()))

    resp: HttpResponse = client.post("/purchase/?q=param", data={"product_id": 999, "quantity": 20})

    # TODO: must be 201
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "q": "param", "product_id": 999, "quantity": 20}


def test_marshmallow_whole_body_post_ok(client, with_urlpatterns, routes: django_hug.Routes):
    class RespSchema(Schema):
        product_id = fields.Int(required=True)
        quantity = fields.Int(required=True)

    @routes.post("<str:name>/")
    def fn(request, name: str, body: RespSchema()):
        loc = locals()
        del loc["request"]
        return loc

    with_urlpatterns(list(routes.urls()))

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123})

    assert resp.status_code == 400, resp.content

    resp: HttpResponse = client.post("/purchase/", data={"product_id": 123, "quantity": 3})
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"name": "purchase", "body": {"product_id": 123, "quantity": 3}}

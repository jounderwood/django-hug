import json

import pytest
from django.http import HttpResponse

from djhug import route
from djhug.routes import Routes
from tests.utils import json_response


def test_register_django_simple_url(client, with_urlpatterns, routes: Routes):
    @routes.get("<int:year>/<str:name>/")
    def view(request, year: int, name: str):
        return json_response(locals())

    with_urlpatterns(routes.get_urlpatterns())
    resp: HttpResponse = client.get("/123/foo/")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": 123, "name": "foo"}


def test_register_django_regex_url(client, with_urlpatterns, routes: Routes):
    @routes.get("api/(?P<year>[0-9]{4})/", re=True)
    def view(request, year: str):
        return json_response(locals())

    with_urlpatterns(routes.get_urlpatterns())
    resp: HttpResponse = client.get("/api/0001/")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"year": "0001"}


def test_only_one_simple_route_per_view():
    with pytest.raises(RuntimeError):
        @route("/")
        @route("/1/")
        def view(*_):
            pass


def test_only_one_django_route_per_view(routes: Routes):
    with pytest.raises(RuntimeError):
        @routes.get("/")
        @routes.get("/1/")
        def view(*_):
            pass

import json
from functools import wraps

import pytest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from djhug.routes import Routes, route
from tests.utils import json_response

test_routes = Routes()


def update_kwargs(fn):
    @wraps(fn)
    def wrap(*args, **kwargs):
        kwargs["from_decorator"] = 1
        return fn(*args, **kwargs)

    return wrap


@test_routes.get("1/")
@update_kwargs
@require_GET
def view_decorated(request, arg: int = 1, **kwargs):
    return json_response(locals())


@require_GET
@update_kwargs
@test_routes.get("2/")
def view_decorated_2(request, arg: int = 1, **kwargs):
    return json_response(locals())


@update_kwargs
@test_routes.get("3/")
@require_GET
def view_decorated_3(request, arg: int = 1, **kwargs):
    return json_response(locals())


@pytest.mark.parametrize("url", ("/1/", "/2/", "/3/"))
def test_wrapped_decorators_ok(client, with_urlpatterns, url):
    with_urlpatterns(test_routes.get_urlpatterns())

    resp: HttpResponse = client.get(url)
    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"arg": 1, "kwargs": {"from_decorator": 1}}

    resp: HttpResponse = client.post(url)
    assert resp.status_code == 405, resp.content


def test_views_got_options():
    assert "arg" in view_decorated.__djhug_options__.spec.arg_types_map
    assert "arg" in view_decorated_2.__djhug_options__.spec.arg_types_map
    assert "arg" in view_decorated_3.__djhug_options__.spec.arg_types_map


def test_decorators_closured_view_ok(client, with_urlpatterns, routes: Routes):
    @update_kwargs
    @routes.get("3/")
    @require_GET
    def view_closure(request, arg: int = 1):
        return json_response(locals())

    with_urlpatterns(routes.get_urlpatterns())
    resp: HttpResponse = client.get("/3/")

    assert resp.status_code == 200, resp.content
    assert json.loads(resp.content) == {"arg": 1}

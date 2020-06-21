from datetime import datetime

from django.http.response import JsonResponse
from pydantic import BaseModel

import djhug
from djhug.content_negotiation import json_renderer

routes = djhug.Routes()


@routes.get("^$", re=True)
def index(request, year: float, name: str, rr: int = 2):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("<int:year>/")
def api_2(request, year, name: int):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("1/<int:year>/")
def api_3(request, year, name: int = "aaa"):
    loc = locals()
    del loc["request"]
    return loc


@djhug.response.camelcased
@djhug.response.renderer(json_renderer)
@routes.get("2/(?P<year>[0-9]{4})/", re=True)
def api_4(request, year, name: int, date: datetime):
    loc = locals()
    del loc["request"]
    return {"some_data": 1, **loc}


class Incoming(BaseModel):
    arg: int


class Outcoming(djhug.Body):
    arg: int


@routes.post("post/", response_model=Outcoming, response_cls=JsonResponse)
def api_5(request, year, name: int, date: datetime, body: Incoming):
    loc = locals()
    del loc["request"]
    return loc


@djhug.route
def api_6(request, arg: str):
    loc = locals()
    del loc["request"]
    return loc

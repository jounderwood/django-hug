from datetime import datetime

from django.http.response import JsonResponse
from pydantic import BaseModel

import djhug

routes = djhug.Routes()


@routes.get("^$", re=True)
def index1(request, year: float, name: str, rr: int = 2):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("<int:year>/")
def index2(request, year, name: int):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("1/<int:year>/")
def index3(request, year, name: int = "aaa"):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("2/(?P<year>[0-9]{4})/", re=True)
def index4(request, year, name: int, date: datetime):
    loc = locals()
    del loc["request"]
    return loc


class Incoming(BaseModel):
    arg: int


class Outcoming(BaseModel):
    arg: int


@routes.post("post/", response_model=Outcoming, response_cls=JsonResponse)
def index5(request, year, name: int, date: datetime, body: Incoming):
    loc = locals()
    del loc["request"]
    return loc


@djhug.route
def index6(request, arg: str):
    loc = locals()
    del loc["request"]
    return loc

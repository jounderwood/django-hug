from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
from marshmallow.validate import Range

import django_hug
from marshmallow import fields

routes = django_hug.Routes()


@routes.get("^$", re=True)
def index2(request, year: float, name: str, rr: int = 2):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("<int:year>/")
def index2(request, year, name: fields.Int(validate=Range(min=1, max=12)) = "aaa"):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("1/<int:year>/")
def index2(request, year, name: int = "aaa"):
    loc = locals()
    del loc["request"]
    return loc


@routes.get("2/(?P<year>[0-9]{4})/", re=True)
def index3(request, year, name:int, date: datetime):
    loc = locals()
    del loc["request"]
    return loc


@django_hug.route()
def index4(request, arg: str):
    loc = locals()
    del loc["request"]
    return loc


# NO ANNOTATIONS BUG
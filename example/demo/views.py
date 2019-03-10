from django.shortcuts import render
from django.http import HttpResponse
import djhug

routes = djhug.Routes()


@routes.get('^$', use_re_path=True)
def index2(request, year: float, name: str, rr: int = 2):
    loc = locals()
    del loc['request']
    return loc


@routes.get('1/<int:year>/')
def index2(request, year, name: int='aaa'):
    loc = locals()
    del loc['request']
    return loc


@routes.get('2/(?P<year>[0-9]{4})/')
def index3(request, year):
    loc = locals()
    del loc['request']
    return loc


@djhug.route()
def index4(request):
    loc = locals()
    del loc['request']
    return loc

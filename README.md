django-hug
==========================
[![Build Status](https://api.cirrus-ci.com/github/jounderwood/django-hug.svg?branch=master)](https://cirrus-ci.com/github/jounderwood/django-hug)
[![Coverage Status](https://coveralls.io/repos/github/jounderwood/django-hug/badge.svg?branch=master)](https://coveralls.io/github/jounderwood/django-hug?branch=master)

Package for working with Django urls/views and request/response validation in more convenient way. 
Inspired by beautiful [hug](https://github.com/timothycrosley/hug).


Getting Started
===================
Simple API building example with django-hug

In your views module create routes and couple API endpoints. 
```python
# views.py
import djhug
from pydantic import PositiveInt

routes = djhug.Routes()


@routes.get('new/<int:year>/')
def simple(request, year, month: int):
    return {"year": year, "month": month}


@routes.get('happy/<int:year>/')
def pydantic_field(request, year, month: PositiveInt = 1):
    return [year, month]
```

In your urls.py specify new endpoints
```python
from .views import routes

urlpatterns = routes.get_urlpatterns()
```

Thats all, now you can make requests to new API endpoints with convenient data validation
```bash
curl http://127.0.0.1:8000/new/2019/?month=133

>> {"year": 2019, "month": 133}
```

Usage
=====
## Regexp path
You can also use regexp path
```python
@routes.get("(?P<year>[0-9]{4})/", re=True)
def index3(request, year, name: str):
    return {"year": year, "name": name}
```

## Request POST data model 
Use `Body` base model to validate whole POST data using whole pydantic Model power

```python
# views.py
import djhug
from pydantic import BaseModel

routes = djhug.Routes(prefix="api")

class RespModel(djhug.Body):
    id: int
    quantity: int


@routes.post("test/")
def view(request, body: RespModel):
    assert isinstance(body, RespModel)
    assert isinstance(body, BaseModel)

    return {"id": body.id}
```

## Camelcase response data and response renderers 
You can enable response data camelcase formatting

```python
# views.py
import djhug
from djhug.content_negotiation import json_renderer

routes = djhug.Routes()


@djhug.response.camelcased
@djhug.response.renderer(json_renderer)
@routes.get("api/(?P<year>[0-9]{4})/", re=True)
def api(request, year, name: int, date: datetime):
    loc = locals()
    del loc["request"]
    return {"some_data": 1, **loc}
```
```bash
curl http://127.0.0.1:8000/api/2000/?name=2&date=2020-10-12T12:00

Content-Type: application/json

{
    "someData": 1,
    "date": "2020-10-12T12:00:00",
    "name": 2,
    "year": "2000"
}
```

## Routes prefix
Specify prefix in Routes object to add prefix to all urls
```python
# views.py
import djhug

routes = djhug.Routes(prefix="api")


@routes.get('<int:year>/')
def api_method(request, year, month: int = 1):
    return {"year": year, "month": month}
```
```bash
curl http://127.0.0.1:8000/api/2019/

>> {"year": 2019, "month": 1}
```

## Settings
```python
DJHUG_RESPONSE_ADDITIONAL_HEADERS = {"Access-Control-Allow-Origin": "*"}
DJHUG_REQUEST_PARSERS_MODULES = ("dotted.path.to.request_parsers",)
DJHUG_RESPONSE_RENDERERS_MODULES = ("dotted.path.to.response_renderers",)
DJHUG_CAMELCASED_RESPONSE_DATA = False
DJHUG_UNDERSCORED_REQUEST_DATA = False
```

## To start example app
```bash
make venv
source activate
cd example
./manage.py runserver
```

## TODO
* Add exception handler
* Docs and example
* Coverage

django-hug
==========================
Package for working with Django urls/views and request/response validation in more convenient way. 
Inspired by beautiful [hug](https://github.com/timothycrosley/hug).


Getting Started
===================
Simple API building example with django-hug

In your views module create routes and couple API endpoints. 
```python
# views.py
import django_hug
from marshmallow import fields

routes = django_hug.Routes()


@routes.get('new/<int:year>/')
def simple(request, year, month: int):
    return {"year": year, "month": month}


@routes.get('happy/<int:year>/')
def mm_field(request, year, month: fields.Int(validate=Range(min=1, max=12)) = 1):
    return [year, month]
```

In your urls.py specify new endpoints
```python
from . import views

urlpatterns = views.routes.urls()
```

Thats all, now you can make requests to new API endpoints with convenient data validation
```bash
curl http://127.0.0.1:8000/new/2019/?month=133

>> {"year": 2019, "month": 133}
```
and nice errors handling
```bash
curl http://127.0.0.1:8000/happy/2019/?month=133

>> {"errors": {"month": ["Must be between 1 and 12."]}}
```

Usage
=====
#### Regexp path
You can also use regexp path
```python
@routes.get("(?P<year>[0-9]{4})/", re=True)
def index3(request, year, name: str):
    loc = locals()
    del loc["request"]
    return loc

```

#### Directives
Use builtin directive `body` to validate whole POST request
```python
# views.py
import django_hug
from marshmallow import Schema, fields

routes = django_hug.Routes(prefix="api")


class RespSchema(Schema):
    id = fields.Int(required=True)
    quantity = fields.Int(required=True)


@routes.post("test/")
def view(request, body: RespSchema()):
    return body
```

#### Routes prefix
Specify prefix in Routes object to add prefix to all urls
```python
# views.py
import django_hug

routes = django_hug.Routes(prefix="api")


@routes.get('<int:year>/')
def api_method(request, year, month: int = 1):
    return {"year": year, "month": month}
```
```bash
curl http://127.0.0.1:8000/api/2019/

>> {"year": 2019, "month": 1}
```

#### Types
__Coming soon__

#### Response and request formatting
Underscore/camelcase transform

__Coming soon__


#### To start example app
```bash
make venv
source activate
cd example
./manage.py runserver
```

Attention! Work In Progress
==
#### TODO
* Full support various view decorators (test_decorators)
* Support multiple routes for one view (?)
* Add exception handler
* Take into account content type for response
* Cleanup tests

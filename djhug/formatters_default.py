import json

from django.core.serializers.json import DjangoJSONEncoder

from djhug import request_formatter, response_formatter


@request_formatter("application/json")
def json_request(request):
    return json.loads(request.body.decode(request.encoding or "utf-8"))


@response_formatter("application/json")
def json_response(response_data) -> str:
    return json.dumps(response_data, cls=DjangoJSONEncoder)

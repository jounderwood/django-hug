from django.http import JsonResponse


def json_response(locals):
    locals.pop("request", None)
    return JsonResponse(locals)

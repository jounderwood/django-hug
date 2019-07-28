import djhug
from djhug.constants import EMPTY
from djhug.routes import Options


def test_req_resp_view_decorators():
    @djhug.response.register_formatter
    def resp_format(data):
        return data

    @djhug.request.register_formatter
    def req_format(request):
        return request.POST

    @djhug.request.format(req_format)
    @djhug.request.underscored
    @djhug.response.format(resp_format)
    @djhug.route
    @djhug.response.camelcased
    def view(request, year: str):
        pass

    assert hasattr(view, "__djhug_options__")
    opts: Options = view.__djhug_options__

    assert opts.underscored_request_data
    assert opts.camelcased_response_data
    assert opts.response_formatter == resp_format
    assert opts.request_formatter == req_format
    assert opts.spec.arg_types_map == {"year": str, "request": EMPTY}

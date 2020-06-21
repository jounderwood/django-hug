import djhug
from djhug.routes import Options


def test_req_resp_view_decorators():
    @djhug.response.register_renderer
    def resp_renderer(data):
        return data

    @djhug.request.register_parser
    def req_parser(request):
        return request.POST

    @djhug.request.parser(req_parser)
    @djhug.request.underscored_body
    @djhug.response.renderer(resp_renderer)
    @djhug.route
    @djhug.response.camelcased
    def view(request, year: str):
        pass

    assert hasattr(view, "__djhug_options__")
    opts: Options = view.__djhug_options__

    assert opts.underscored_body_data
    assert opts.camelcased_response_data
    assert opts.response_renderer == resp_renderer
    assert opts.request_parser == req_parser
    assert opts.spec.arg_types_map == {"year": str, "request": None}

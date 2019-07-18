from marshmallow import fields

from djhug.arguments import Spec
from djhug.routes import route, ViewOptions


def test_options_contribute():
    @route
    def view(request, year: int, name: str, q1: float = 0, q2: str = "firefire") -> dict:
        return locals()

    opts = view.__djhug_options__
    assert isinstance(opts, ViewOptions)
    assert isinstance(opts.spec, Spec)
    assert [arg.name for arg in opts.spec.args] == ["request", "year", "name", "q1", "q2"]


def test_options_contribute_decorator_call():
    @route(uuu=1)
    def view(a=1) -> dict:
        return locals()

    assert isinstance(view.__djhug_options__, ViewOptions)


def test_route_args_override():
    @route(args={"a": fields.Int()})
    def view(a: int = 1) -> dict:
        return locals()

    assert isinstance(view.__djhug_options__.spec.arg_types_map["a"], fields.Int)

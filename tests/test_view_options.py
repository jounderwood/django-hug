from datetime import datetime

from djhug import route
from djhug.arguments import Spec, Arg, Body
from djhug.constants import EMPTY
from djhug.routes import Options


def test_options_contribute():
    @route
    def view(request, generic: int) -> dict:
        return locals()

    opts = view.__djhug_options__
    assert isinstance(opts, Options)
    assert isinstance(opts.spec, Spec)


def test_view_inspect_args():
    @route
    def view(request, generic: int, no_annotation, date: datetime, *args, with_default: str = "foo", **kwargs) -> dict:
        return locals()

    opts = view.__djhug_options__
    assert isinstance(opts, Options)
    assert isinstance(opts.spec, Spec)

    assert opts.spec.args == [
        Arg(name="request", type=None, default=EMPTY),
        Arg(name="generic", type=int, default=EMPTY),
        Arg(name="no_annotation", type=None, default=EMPTY),
        Arg(name="date", type=datetime, default=EMPTY),
        Arg(name="with_default", type=str, default="foo"),
    ]


def test_view_inspect_body():
    class ResponseModel(Body):
        arg: int

    @route
    def view(request, data: ResponseModel):
        return {}

    opts = view.__djhug_options__

    assert opts.spec.body_name == "data"
    assert opts.spec.body_model is ResponseModel


def test_options_contribute_decorator_call():
    @route(uuu=1)
    def view(a=1) -> dict:
        return locals()

    assert isinstance(view.__djhug_options__, Options)

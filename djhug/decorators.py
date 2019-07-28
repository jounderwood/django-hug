from functools import wraps
from typing import Optional, Dict, Callable

from djhug.middleware import ViewWrapper
from djhug.options import Options
from djhug.utils import decorator_with_arguments, get_unwrapped_function


@decorator_with_arguments
def route(fn: Callable, *_, args: Optional[Dict[str, any]] = None, **__):
    Options.register(fn, args=args)
    return wraps(fn)(ViewWrapper(fn))


@decorator_with_arguments
def with_camelcased_response(fn: Callable):
    opts = Options.get_or_contribute(get_unwrapped_function(fn))
    opts.camelcased_response_data = True
    return fn


@decorator_with_arguments
def with_underscored_request(fn: Callable):
    opts = Options.get_or_contribute(get_unwrapped_function(fn))
    opts.underscored_request_data = True
    return fn


def with_request_format(formatter: Callable = None):
    def wrapper(fn: Callable):
        opts = Options.get_or_contribute(get_unwrapped_function(fn))
        opts.set_request_formatter(formatter)
        return fn

    return wrapper


def with_response_format(formatter: Callable = None):
    def wrapper(fn: Callable):
        opts = Options.get_or_contribute(get_unwrapped_function(fn))
        opts.set_response_formatter(formatter)
        return fn
    return wrapper

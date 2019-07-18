from functools import wraps
from typing import Callable


def decorator_with_arguments(function: Callable):
    """
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    https://stackoverflow.com/a/14412901
    """
    @wraps(function)
    def new_decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return function(args[0])
        else:
            # decorator arguments
            return lambda real_function: function(real_function, *args, **kwargs)

    return new_decorator

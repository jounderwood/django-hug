import re
from functools import partial
from functools import wraps
from typing import Callable, Union

UNDERSCORE = (re.compile("(.)([A-Z][a-z]+)"), re.compile("([a-z0-9])([A-Z])"))


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


def get_unwrapped_function(fn):
    while True:
        wrapped = getattr(fn, "__wrapped__", None)
        if wrapped is None:
            break
        fn = wrapped
    return fn


def underscore_text(text: str):
    """Converts text that may be camelcased into an underscored format"""
    return UNDERSCORE[1].sub(r"\1_\2", UNDERSCORE[0].sub(r"\1_\2", text)).lower()


def camelcase_text(text: str):
    """Converts text that may be underscored into a camelcase format"""
    return text[0] + "".join(text.title().split("_"))[1:]


def _transform(content: Union[str, dict, list], transformator):
    if isinstance(content, dict):
        new_dictionary = {}
        for key, value in content.items():
            if isinstance(key, str):
                key = transformator(key)
            new_dictionary[key] = _transform(value, transformator)
        return new_dictionary
    elif isinstance(content, list):
        new_list = []
        for element in content:
            new_list.append(_transform(element, transformator))
        return new_list
    elif isinstance(content, str):
        return transformator(content)
    else:
        return content


camelcase = partial(_transform, transformator=camelcase_text)
underscore = partial(_transform, transformator=underscore_text)

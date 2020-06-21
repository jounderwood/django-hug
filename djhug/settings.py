from importlib import import_module
from typing import Dict, Any, Iterable
from typing import Optional

from django.conf import settings as global_settings


class Settings:
    __shared_state: Dict[str, Any] = {}

    response_additional_headers: Optional[Dict[str, str]] = None

    request_parsers_modules: Optional[Iterable[str]] = None
    response_renderers_modules: Optional[Iterable[str]] = None

    camelcased_response_data: bool = False
    underscored_request_data: bool = False

    def __init__(self):
        self.__dict__ = self.__shared_state

        self._prefix = "djhug_"

        for var in dir(self.__class__):
            if not var.startswith("_"):
                try:
                    final_setting = getattr(global_settings, self._get_setting_name(var))
                except AttributeError:
                    pass
                else:
                    setattr(self, var, final_setting)

        self.response_additional_headers = self.response_additional_headers or {}

        _bulk_import(self.request_parsers_modules)
        _bulk_import(self.response_renderers_modules)

    def _get_setting_name(self, setting):
        return ("%s%s" % (self._prefix, setting)).upper()


def _bulk_import(paths: Iterable[str]):
    if paths:
        for path in paths:
            import_module(path)

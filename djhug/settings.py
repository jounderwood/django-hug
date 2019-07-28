from typing import Dict
from typing import List, Optional

from django.conf import settings as global_settings
from django.utils.module_loading import import_string

from djhug.format import is_valid_request_formatter, is_valid_response_formatter


class Settings:
    response_additional_headers: Dict[str, str] = None

    request_formatters: Optional[List[str]] = None
    response_formatters: Optional[List[str]] = None

    camelcased_response_data: bool = False
    underscored_request_data: bool = False

    def __init__(self):
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

        self._register_formatters("request_formatters", is_valid_request_formatter)
        self._register_formatters("response_formatters", is_valid_response_formatter)

    def _get_setting_name(self, setting):
        return ("%s%s" % (self._prefix, setting)).upper()

    def _register_formatters(self, attr_name, validator):
        formatters: Optional[List[str]] = getattr(self, attr_name)

        if not formatters:
            return

        for formatter in formatters:
            if isinstance(formatter, str):
                formatter = import_string(formatter)

            if not validator(formatter):
                raise ValueError(
                    "Setting %s value %r is not valid, formatter must be function decorated with "
                    "`djhug.formatter` decorator" % (self._get_setting_name(attr_name), formatter)
                )


settings = Settings()

import sys

import django
import pytest
from django.test import override_settings

import django_hug

urlpatterns = []  # noqa


def pytest_addoption(parser):
    parser.addoption(
        "--no-pkgroot",
        action="store_true",
        default=False,
    )
    parser.addoption(
        "--staticfiles",
        action="store_true",
        default=False,
    )


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        SITE_ID=1,
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL="/static/",
        ROOT_URLCONF=__name__,
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {"debug": True},  # We want template errors to raise
            }
        ],
        MIDDLEWARE=(
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ),
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.staticfiles",
        ),
        PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
    )

    django.setup()


@pytest.fixture
def with_urlpatterns(monkeypatch):
    with override_settings(ROOT_URLCONF=__name__):
        mod = sys.modules[__name__]

        def wrap(urlpatterns):
            mod.urlpatterns = []
            monkeypatch.setattr(mod, "urlpatterns", list(urlpatterns))

        yield wrap


@pytest.fixture
def routes():
    return django_hug.Routes()

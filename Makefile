PROJECT = django-hug

PYTHON_VER = python3.7
PYTHON_SYSTEM_PATH = "$(readlink $(which $(PYTHON_VER)))"

REQUIREMENTS = requirements.txt
REQUIREMENTS_DEV = requirements-dev.txt
VIRTUAL_ENV := $(dir $(abspath $(lastword $(MAKEFILE_LIST)))).venv$(PYTHON_VERSION)
PYTHON := $(VIRTUAL_ENV)/bin/python
PIP_CONF = pip.conf
PYPI = dev
TEST_SETTINGS = settings_test


tests: venv
	$(VIRTUAL_ENV)/bin/py.test

tests_coverage: venv
	$(VIRTUAL_ENV)/bin/py.test --cov-report html:.reports/coverage --cov-config .coveragerc --cov-report term:skip-covered --cov djhug

venv_init:
	if [ ! -d $(VIRTUAL_ENV) ]; then \
		virtualenv -p $(PYTHON_SYSTEM_PATH) --prompt="($(PROJECT)) " $(VIRTUAL_ENV); \
	fi

venv:  venv_init
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS)
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS_DEV)
	ln -sf $(VIRTUAL_ENV)/bin/activate activate


clean_venv:
	rm -rf $(VIRTUAL_ENV)

clean_pyc:
	find . -name \*.pyc -delete

clean: clean_venv clean_pyc

package:
	$(PYTHON) setup.py sdist

pkg_upload:
	$(PYTHON) setup.py sdist upload -r $(PYPI)

pkg_register:
	$(PYTHON) setup.py sdist register -r $(PYPI)

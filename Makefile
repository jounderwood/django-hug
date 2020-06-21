PROJECT = djhug

PYTHON_VER = python3.7
PYTHON_SYSTEM_PATH = "$(readlink $(which $(PYTHON_VER)))"

REQUIREMENTS = requirements.txt
REQUIREMENTS_DEV = requirements-dev.txt
VIRTUAL_ENV := $(dir $(abspath $(lastword $(MAKEFILE_LIST)))).venv
PYTHON := $(VIRTUAL_ENV)/bin/python
TEST_PYPI = https://test.pypi.org/legacy/


venv_init:
	pip install virtualenv
	if [ ! -d $(VIRTUAL_ENV) ]; then \
		virtualenv -p $(PYTHON_SYSTEM_PATH) --prompt="($(PROJECT)) " $(VIRTUAL_ENV); \
	fi

venv:  venv_init
	pip install -r $(REQUIREMENTS)
	pip install -r $(REQUIREMENTS_DEV)
	ln -sf $(VIRTUAL_ENV)/bin/activate activate


tests: venv
	$(VIRTUAL_ENV)/bin/py.test

tests_coverage: venv
	$(VIRTUAL_ENV)/bin/py.test --cov $(PROJECT) --cov-report html

lint:
	$(VIRTUAL_ENV)/bin/black -l 120 --check $(PROJECT)

coveralls:
	$(VIRTUAL_ENV)/bin/coveralls


clean_venv:
	rm -rf $(VIRTUAL_ENV)

clean_pyc:
	find . -name \*.pyc -delete

clean: clean_venv clean_pyc

package:
	$(PYTHON) setup.py sdist bdist_wheel

pkg_upload:
	twine upload dist/*

pkg_upload_test:
	twine upload --repository-url $(TEST_PYPI) dist/*

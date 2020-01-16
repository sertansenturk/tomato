SHELL := /bin/bash
.PHONY: \
	purge clean-all clean clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin \
	install \
	docker-build docker-build-test docker-run-import docker-run-tests

VENV_INTERP = python3.6
VENV_NAME ?= venv

PIP_INST_EXTRA = 
PIP_INST_DEV = development
PIP_INST_DEMO = demo
PIP_INST_ALL = $(PIP_INST_DEV),$(PIP_INST_DEMO)
PIP_INST_FLAG = 
PIP_INST_EDIT = -e

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_TEST_TAG = $(DOCKER_TAG)-test
DOCKER_TEST_VER = $(DOCKER_VER)
DOCKER_TEST_FILE = docker/tests/Dockerfile

HELP_PADDING = 18
help:
	@printf "===== Cleanup =====\n"
	@printf "clean             : remove all build, test, coverage and Python artifacts\n"
	@printf "clean-all, purge  : remove all (see: clean), plus virtualenv, and tomato binaries\n"
	@printf "	virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\"\n"
	@printf "clean-build       : remove build artifacts\n"
	@printf "clean-pyc         : remove Python file artifacts\n"
	@printf "clean-test        : remove test artifacts\n"
	@printf "%-$(HELP_PADDING)s: remove Python virtualenv folder\n" clean-$(VENV_NAME)
	@printf "	virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\"\n"
	@printf "clean-bin         : remove tomato binaries\n"
	@printf "===== Python ======\n"
	@printf "%-$(HELP_PADDING)s: create a virtualenv\n" $(VENV_NAME)
	@printf "	virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\"\n"
	@printf "	Python interpreter: \"VENV_INTERP = $(VENV_INTERP)\"\n"
	@printf "install           : install tomato\n"
	@printf "	virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\"\n"
	@printf "	pip install flags: \"PIP_INST_FLAG = $(PIP_INST_FLAG)\"\n"
	@printf "	pip install extras_require: \"PIP_INST_EXTRA = $(PIP_INST_EXTRA)\")\n" $(VENV_NAME)
	@printf "install-development : \n"
	@printf "install-demo  : \n"
	@printf "install-all  : \n"
	@printf "install-editable  : \n"
	@printf "install-editable-development : \n"
	@printf "install-editable-demo  : \n"
	@printf "install-editable-all  : \n"
	@printf "===== Docker ======\n"
	@printf "docker-build      : build docker image\n"
	@printf "	tag: \"DOCKER_TAG = $(DOCKER_TAG)\"\n"
	@printf "	version: \"DOCKER_VER = $(DOCKER_VER)\"\n"
	@printf "docker-build-test : build a docker image with tests\n"
	@printf "	tag: \"DOCKER_TEST_TAG = $(DOCKER_TEST_TAG)\"\n"
	@printf "	version: \"DOCKER_TEST_VER = $(DOCKER_TEST_VER)\"\n"
	@printf "docker-run-import : run a dummy import script inside docker\n"
	@printf "docker-run-tests  : run the tests inside docker\n"

purge: clean-all

clean-all: clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin

clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build: ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '.eggs' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-$(VENV_NAME):
	rm -rf $(VENV_NAME)

clean-bin:
	rm -rf tomato/bin/phraseSeg tomato/bin/extractTonicTempoTuning tomato/bin/alignAudioScore tomato/bin/MusikiToMusicXml	

$(VENV_NAME):
	python3 -m virtualenv -p $(VENV_INTERP) $(VENV_NAME)

install: 
	source $(VENV_NAME)/bin/activate ; \
	pip install --upgrade pip ; \
	if [ "$(PIP_INST_EXTRA)" = "" ]; then \
        python -m pip install $(PIP_INST_FLAG) .; \
	else \
	    python -m pip install $(PIP_INST_FLAG) .[$(PIP_INST_EXTRA)] ; \
    fi

install-editable: PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-editable: install

install-$(PIP_INST_DEMO): PIP_INST_EXTRA:=$(PIP_INST_DEMO)
install-$(PIP_INST_DEMO): install

install-editable-$(PIP_INST_DEMO): PIP_INST_EXTRA:=$(PIP_INST_DEMO)
install-editable-$(PIP_INST_DEMO): PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-editable-$(PIP_INST_DEMO): install

install-$(PIP_INST_DEV): PIP_INST_EXTRA:=$(PIP_INST_DEV)
install-$(PIP_INST_DEV): install

install-editable-$(PIP_INST_DEV): PIP_INST_EXTRA:=$(PIP_INST_DEV)
install-editable-$(PIP_INST_DEV): PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-editable-$(PIP_INST_DEV): install

install-all: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-all: install

install-editable-all: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-editable-all: PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-editable-all: install

docker-build:
	docker build . -t $(DOCKER_TAG):$(DOCKER_VER)

docker-build-test: docker-build
	docker build . \
		-f $(DOCKER_TEST_FILE) \
		-t $(DOCKER_TEST_TAG):$(DOCKER_TEST_VER)

docker-run-import: docker-build
	docker run \
		$(DOCKER_TAG):$(DOCKER_VER) \
		python3 -c \
			"import tomato.symbolic.symbtrconverter; \
			import tomato.symbolic.symbtranalyzer; \
			import tomato.audio.audioanalyzer; \
			import tomato.joint.jointanalyzer; \
			import tomato.joint.completeanalyzer"

docker-run-tests: docker-build-test
	docker run \
		$(DOCKER_TEST_TAG):$(DOCKER_TEST_VER) \
		python3 -m pytest tests

# isort:
# 	sh -c "isort --skip-glob=.tox --recursive . "

# lint:
# 	flake8 --exclude=.tox

# black:
# 	black --line-length 79 ./

# test: clean-pyc
# 	py.test --verbose --color=yes $(TEST_PATH)


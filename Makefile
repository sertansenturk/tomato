SHELL := /bin/bash
.DEFAULT_GOAL := all
.PHONY: \
	purge clean-all clean clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin \
	install install-$(PIP_INST_DEV) install-$(PIP_INST_DEMO) install-all install-all-editable \
	docker-build docker-run-import docker-run-tests \
	all

VENV_INTERP = python3.6
VENV_NAME ?= venv

PIP_INST_EXTRA = 
PIP_INST_DEV = development
PIP_INST_DEMO = demo
PIP_INST_ALL = $(PIP_INST_DEV),$(PIP_INST_DEMO)
PIP_FLAG = 
PIP_INST_FLAG = 
PIP_INST_EDIT = -e

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_TEST = false
DOCKER_TEST_VER = $(DOCKER_VER)
DOCKER_TEST_TAG = $(DOCKER_TAG)-test
DOCKER_TEST_FILE = docker/tests/Dockerfile

HELP_PADDING = 21
bold := $(shell tput bold)
sgr0 := $(shell tput sgr0)
padded_str := %-$(HELP_PADDING)s
pretty_command := $(bold)$(padded_str)$(sgr0)

help:
	@printf "======= Default ======\n"
	@printf "$(pretty_command): install tomato in editable mode with all extra dependencies\n"
	@printf "$(pretty_command): default target; alias of \"install-all-editable\"\n" all
	@printf "\n"
	@printf "======= Cleanup ======\n"
	@printf "$(pretty_command): remove all build, test, coverage and python artifacts\n" clean
	@printf "$(pretty_command): remove all (see: \"clean\") plus virtualenv, and tomato binaries\n" clean-all
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): alias of \"clean-all\"\n" purge
	@printf "$(pretty_command): remove tomato binaries\n" clean-bin
	@printf "$(pretty_command): remove build artifacts\n" clean-build
	@printf "$(pretty_command): remove python file artifacts\n" clean-pyc
	@printf "$(pretty_command): remove test artifacts\n" clean-test
	@printf "$(pretty_command): remove python virtualenv folder\n" clean-$(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "\n"
	@printf "======= Python =======\n"
	@printf "$(pretty_command): create a virtualenv\n" $(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(padded_str)VENV_INTERP, python interpreter (default: $(VENV_INTERP))\n"
	@printf "$(pretty_command): install tomato to virtualenv, creates the virtualenv if it does not exist\n" install
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(padded_str)PIP_INST_EXTRA, install from extras_require (default: $(PIP_INST_EXTRA), possible values: $(PIP_INST_ALL))\n"
	@printf "$(pretty_command): install tomato with development dependencies, creates the virtualenv if it does not exist\n" install-$(PIP_INST_DEV)
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato with demo dependencies, creates the virtualenv if it does not exist\n" install-$(PIP_INST_DEMO)
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato with all dependencies, creates the virtualenv if it does not exist\n" install-all
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in editable mode with all extra dependencies, creates the virtualenv if it does not exist\n" install-all-editable
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "\n"
	@printf "======= Docker =======\n"
	@printf "$(pretty_command): build docker image\n" docker-build
	@printf "$(padded_str)DOCKER_TAG, docker image tag (default: $(DOCKER_TAG))\n"
	@printf "$(padded_str)DOCKER_VER, docker image version (default: $(DOCKER_VER))\n"
	@printf "$(padded_str)DOCKER_TEST, boolean flag to build an extended docker image with tests (default: $(DOCKER_TEST))\n"
	@printf "$(padded_str)DOCKER_TEST_TAG, test docker image tag (default: $(DOCKER_TEST_TAG))\n"
	@printf "$(padded_str)DOCKER_TEST_VER, test docker image version (default $(DOCKER_TEST_VER))\n"
	@printf "$(pretty_command): run a dummy import script inside docker\n" docker-run-import
	@printf "$(pretty_command): run the tests inside docker\n" docker-run-tests

all: install-all-editable

purge: clean-all

clean-all: clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin

clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-bin:
	rm -rf tomato/bin/phraseSeg tomato/bin/extractTonicTempoTuning tomato/bin/alignAudioScore tomato/bin/MusikiToMusicXml	

clean-build: ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	rm -rf .pytest_cache
	find . -name '.eggs' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-$(VENV_NAME):
	rm -rf $(VENV_NAME)

$(VENV_NAME):
	python3 -m virtualenv -p $(VENV_INTERP) $(VENV_NAME)

install:
	source $(VENV_NAME)/bin/activate ; \
	pip install --upgrade pip ; \
	if [ "$(PIP_INST_EXTRA)" = "" ]; then \
        python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .; \
	else \
	    python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .[$(PIP_INST_EXTRA)]; \
    fi

install-$(PIP_INST_DEMO): PIP_INST_EXTRA:=$(PIP_INST_DEMO)
install-$(PIP_INST_DEMO): install

install-$(PIP_INST_DEV): PIP_INST_EXTRA:=$(PIP_INST_DEV)
install-$(PIP_INST_DEV): install

install-all: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-all: install

install-all-editable: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-all-editable: PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-all-editable: install

docker-build:
	docker build . -t $(DOCKER_TAG):$(DOCKER_VER)
	if [ "$(DOCKER_TEST)" = true ]; then \
        docker build . \
			-f $(DOCKER_TEST_FILE) \
			-t $(DOCKER_TEST_TAG):$(DOCKER_TEST_VER); \
	fi

docker-run-import: docker-build
	docker run \
		$(DOCKER_TAG):$(DOCKER_VER) \
		python3 -c \
			"import tomato.symbolic.symbtrconverter; \
			import tomato.symbolic.symbtranalyzer; \
			import tomato.audio.audioanalyzer; \
			import tomato.joint.jointanalyzer; \
			import tomato.joint.completeanalyzer"

docker-run-tests: DOCKER_TEST:=true
docker-run-tests: docker-build
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


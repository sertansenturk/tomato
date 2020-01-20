SHELL := /bin/bash
.DEFAULT_GOAL := default
.PHONY: \
	help default dev all-editable \
	clean clean-all clean-bin clean-build clean-pyc clean-test \
	clean-$(VENV_NAME) clean-$(DEV_VENV_NAME) purge \
	install install-all install-all-editable \
	install-requirements install-dev-requirements \
	install-mcr install-tomato \
	docker-build test test-docker lint flake8 pylint isort

BIN_DOWN_DIR = src/tomato/bin

VENV_INTERP = python3.6
VENV_NAME ?= venv
DEV_VENV_NAME ?= venv-dev

PIP_INST_EXTRA = 
PIP_INST_DEV = development
PIP_INST_DEMO = demo
PIP_INST_ALL = $(PIP_INST_DEV),$(PIP_INST_DEMO)
PIP_FLAG = 
PIP_INST_FLAG = 
PIP_INST_EDIT = -e

REQUIREMENTS_FILE = requirements.txt
DEV_REQUIREMENTS_FILE = requirements.dev.txt

MCR_DOWN_URL = http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip
MCR_DOWNLOAD_PATH = /tmp/mcr-install
MCR_INST_PATH = /usr/local/MATLAB/MATLAB_Runtime/
MCR_PATH = $(MCR_INST_PATH)v85

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_FILE = Dockerfile
DOCKER_FLAG = 

HELP_PADDING = 28
bold := $(shell tput bold)
sgr0 := $(shell tput sgr0)
padded_str := %-$(HELP_PADDING)s
pretty_command := $(bold)$(padded_str)$(sgr0)

help:
	@printf "======= General ======\n"
	@printf "$(pretty_command): run \"default\" (see below)\n"
	@printf "$(pretty_command): run \"clean-all\", \"$(VENV_NAME)\", and \"install\"\n" default
	@printf "$(pretty_command): run \"clean-all\", \"$(DEV_VENV_NAME)\", and \"install-dev-requirements\"\n" dev
	@printf "$(pretty_command): run \"clean-all\", \"$(VENV_NAME)\", and \"install-all-editable\"\n" all-editable
	@printf "\n"
	@printf "======= Cleanup ======\n"
	@printf "$(pretty_command): remove all build, test, coverage and python artifacts\n" clean
	@printf "$(pretty_command): \"clean\" (see: above) plus virtualenv, and tomato binaries\n" clean-all
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): remove tomato binaries\n" clean-bin
	@printf "$(pretty_command): remove build artifacts\n" clean-build
	@printf "$(pretty_command): remove python file artifacts\n" clean-pyc
	@printf "$(pretty_command): remove test artifacts\n" clean-test
	@printf "$(pretty_command): remove python virtualenv\n" clean-$(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): remove python development virtualenv\n" clean-$(DEV_VENV_NAME)
	@printf "$(padded_str)DEV_VENV_NAME, development virtualenv name (default: $(DEV_VENV_NAME))\n"
	@printf "$(pretty_command): \"clean-all\" plus development virtualenv\n" purge
	@printf "\n"
	@printf "======= Setup =======\n"
	@printf "$(pretty_command): create a virtualenv\n" $(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(padded_str)VENV_INTERP, python interpreter (default: $(VENV_INTERP))\n"
	@printf "$(pretty_command): create a development virtualenv\n" $(DEV_VENV_NAME)
	@printf "$(padded_str)DEV_VENV_NAME, development virtualenv name (default: $(DEV_VENV_NAME))\n"
	@printf "$(padded_str)VENV_INTERP, python interpreter (default: $(VENV_INTERP))\n"
	@printf "$(pretty_command): install tomato in a virtualenv, and install MCR\n" install
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in a virtualenv with all extra dependencies, and install MCR\n" install-all
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in editable mode and in a virtualenv with all extra dependencies, and install MCR\n" install-all-editable
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(pretty_command): install LilyPond\n" install-lilypond
	@printf "$(pretty_command): install MATLAB Runtime Compiler (MCR)\n" install-mcr
	@printf "$(padded_str)MCR_DOWNLOAD_PATH, temporary folder to download MCR into (default: $(MCR_DOWNLOAD_PATH))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(pretty_command): install libraries in $(REQUIREMENTS_FILE) to the virtualenv\n" install-requirements
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): install development libraries in $(DEV_REQUIREMENTS_FILE) to the virtualenv\n" install-dev-requirements
	@printf "$(padded_str)DEV_VENV_NAME, development virtualenv name to install (default: $(DEV_VENV_NAME))\n"
	@printf "$(pretty_command): install tomato in a virtualenv\n" install-tomato
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(padded_str)PIP_INST_EXTRA, install from extras_require (default: $(PIP_INST_EXTRA), possible values: $(PIP_INST_ALL))\n"
	@printf "\n"
	@printf "======= Docker =======\n"
	@printf "$(pretty_command): build docker image\n" docker-build
	@printf "$(padded_str)DOCKER_TAG, docker image tag (default: $(DOCKER_TAG))\n"
	@printf "$(padded_str)DOCKER_VER, docker image version (default: $(DOCKER_VER))\n"
	@printf "$(padded_str)DOCKER_FLAG, additional docker build flags (default: $(DOCKER_FLAG))\n"
	@printf "\n"
	@printf "======= Test and linting =======\n"
	@printf "$(pretty_command): run all test and linting automations using tox\n" test
	@printf "$(pretty_command): run docker build and test automation using tox\n" test-docker
	@printf "$(pretty_command): run all style checking and linting automation using tox \n" lint
	@printf "$(pretty_command): run flake8 for style guide (PEP8) checking using tox\n" flake8
	@printf "$(pretty_command): run pylint using tox\n" pylint
	@printf "$(pretty_command): sorts python imports\n" isort

default: clean-all $(VENV_NAME) install

dev: VENV_NAME:=$(DEV_VENV_NAME)
dev: clean-$(DEV_VENV_NAME) $(DEV_VENV_NAME) install-dev-requirements

all-editable: clean-all $(VENV_NAME) install-all-editable

purge: clean-all clean-$(DEV_VENV_NAME)

clean-all: clean-pyc clean-build clean-test \
	clean-bin clean-$(VENV_NAME)

clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-bin:
	rm -rf $(BIN_DOWN_DIR)/phraseSeg \
		$(BIN_DOWN_DIR)/extractTonicTempoTuning \
		$(BIN_DOWN_DIR)/alignAudioScore \
		$(BIN_DOWN_DIR)/MusikiToMusicXml

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

clean-$(DEV_VENV_NAME):
	rm -rf $(DEV_VENV_NAME)

$(VENV_NAME):
	python3 -m virtualenv -p $(VENV_INTERP) $(VENV_NAME)

$(DEV_VENV_NAME):
	python3 -m virtualenv -p $(VENV_INTERP) $(DEV_VENV_NAME)

install: install-lilypond install-mcr install-tomato

install-all: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-all: install

install-all-editable: PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-all-editable: install-all

install-requirements: $(VENV_NAME)
	source $(VENV_NAME)/bin/activate ; \
	pip install -r $(REQUIREMENTS_FILE)

install-dev-requirements: $(DEV_VENV_NAME)
	source $(DEV_VENV_NAME)/bin/activate ; \
	pip install -r $(DEV_REQUIREMENTS_FILE)

install-tomato: $(VENV_NAME)
	source $(VENV_NAME)/bin/activate ; \
	pip install --upgrade pip ; \
	if [ "$(PIP_INST_EXTRA)" = "" ]; then \
        python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .; \
	else \
	    python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .[$(PIP_INST_EXTRA)]; \
    fi

install-mcr:
	if [ -z "$$(ls -A $(MCR_PATH))" ]; then \
		echo "Installing MCR to $(MCR_PATH)..."; \
		mkdir $(MCR_DOWNLOAD_PATH) ; \
		cd $(MCR_DOWNLOAD_PATH) ; \
		wget --progress=bar:force $(MCR_DOWN_URL) ; \
		unzip -q MCR_R2015a_glnxa64_installer.zip ; \
		$(MCR_DOWNLOAD_PATH)/install \
			-destinationFolder $(MCR_INST_PATH) \
			-agreeToLicense yes \
			-mode silent ; \
		cd / ; \
		rm -rf $(MCR_DOWNLOAD_PATH) ; \
	else \
		echo "MCR is already installed to $(MCR_PATH). Skipping..."; \
    fi

install-lilypond:
	sudo apt -qq install -y lilypond

docker-build:
	docker build . \
		-f $(DOCKER_FILE) \
		-t $(DOCKER_TAG):$(DOCKER_VER) \
		$(DOCKER_FLAG)

test:
	tox

test-docker:
	tox -e docker

lint:
	tox -e lint

flake8:
	tox -e flake8

pylint:
	tox -e pylint

isort:
	isort --skip-glob=.tox --recursive . 

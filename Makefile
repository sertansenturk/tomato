SHELL := /bin/bash
.DEFAULT_GOAL := default
.PHONY: \
	clean clean-all clean-bin clean-build clean-pyc clean-test clean-$(VENV_NAME) purge\
	install install-all install-all-editable install-mcr install-tomato \
	install-tomato-$(PIP_INST_DEV) install-tomato-$(PIP_INST_DEMO) \
	docker-build docker-run-import docker-run-tests \
	default all-editable

VENV_INTERP = python3.6
VENV_NAME ?= venv

PIP_INST_EXTRA = 
PIP_INST_DEV = development
PIP_INST_DEMO = demo
PIP_INST_ALL = $(PIP_INST_DEV),$(PIP_INST_DEMO)
PIP_FLAG = 
PIP_INST_FLAG = 
PIP_INST_EDIT = -e

MCR_DOWN_URL = http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip
MCR_DOWNLOAD_PATH = /tmp/mcr-install
MCR_INST_PATH = /usr/local/MATLAB/MATLAB_Runtime/
MCR_PATH = $(MCR_INST_PATH)v85

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_TEST_VER = $(DOCKER_VER)
DOCKER_TEST_TAG = $(DOCKER_TAG)-test
DOCKER_TEST_FILE = docker/tests/Dockerfile

HELP_PADDING = 28
bold := $(shell tput bold)
sgr0 := $(shell tput sgr0)
padded_str := %-$(HELP_PADDING)s
pretty_command := $(bold)$(padded_str)$(sgr0)

help:
	@printf "======= Default ======\n"
	@printf "$(pretty_command): run \"default\" (see below)\n"
	@printf "$(pretty_command): run \"clean-all\", \"$(VENV_NAME)\", and \"install\" sequentially\n" default
	@printf "$(pretty_command): run \"clean-all\", \"$(VENV_NAME)\", and \"install-all-editable\" sequentially\n" all-editable
	@printf "\n"
	@printf "======= Cleanup ======\n"
	@printf "$(pretty_command): remove all build, test, coverage and python artifacts\n" clean
	@printf "$(pretty_command): remove all (see: above) plus virtualenv, and tomato binaries\n" clean-all
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): remove tomato binaries\n" clean-bin
	@printf "$(pretty_command): remove build artifacts\n" clean-build
	@printf "$(pretty_command): remove python file artifacts\n" clean-pyc
	@printf "$(pretty_command): remove test artifacts\n" clean-test
	@printf "$(pretty_command): remove python virtualenv folder\n" clean-$(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(pretty_command): alias of \"clean-all\"\n" purge
	@printf "\n"
	@printf "======= Setup =======\n"
	@printf "$(pretty_command): install tomato in a virtualenv, and install MCR\n" install
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in a virtualenv with all python dependencies, and install MCR\n" install-all
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in editable mode and in a virtualenv with all python dependencies, and install MCR\n" install-all-editable
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(pretty_command): install MATLAB Runtime Compiler (MCR)\n" install-mcr
	@printf "$(padded_str)MCR_DOWNLOAD_PATH, temporary folder to download MCR into (default: $(MCR_DOWNLOAD_PATH))\n"
	@printf "$(padded_str)MCR_INST_PATH, path to install MCR (default: $(MCR_INST_PATH))\n"
	@printf "$(pretty_command): install tomato in a virtualenv\n" install-tomato
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(padded_str)PIP_INST_EXTRA, install from extras_require (default: $(PIP_INST_EXTRA), possible values: $(PIP_INST_ALL))\n"
	@printf "$(pretty_command): install tomato in a virtualenv with python development dependencies\n" install-tomato-$(PIP_INST_DEV)
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): install tomato in a virtualenv with python demo dependencies\n" install-tomato-$(PIP_INST_DEMO)
	@printf "$(padded_str)VENV_NAME, virtualenv name to install (default: $(VENV_NAME))\n"
	@printf "$(padded_str)PIP_FLAG, pip flags (default: $(PIP_FLAG))\n"
	@printf "$(padded_str)PIP_INST_FLAG, pip install flags (default: $(PIP_INST_FLAG))\n"
	@printf "$(pretty_command): create a virtualenv\n" $(VENV_NAME)
	@printf "$(padded_str)VENV_NAME, virtualenv name (default: $(VENV_NAME))\n"
	@printf "$(padded_str)VENV_INTERP, python interpreter (default: $(VENV_INTERP))\n"
	@printf "\n"
	@printf "======= Docker =======\n"
	@printf "$(pretty_command): build docker image\n" docker-build
	@printf "$(padded_str)DOCKER_TAG, docker image tag (default: $(DOCKER_TAG))\n"
	@printf "$(padded_str)DOCKER_VER, docker image version (default: $(DOCKER_VER))\n"
	@printf "$(pretty_command): build an extended docker image with pytests \n" docker-build-test
	@printf "$(padded_str)DOCKER_TEST_TAG, test docker image tag (default: $(DOCKER_TEST_TAG))\n"
	@printf "$(padded_str)DOCKER_TEST_VER, test docker image version (default $(DOCKER_TEST_VER))\n"
	@printf "$(pretty_command): run a dummy import script inside docker, build the docker image if it does not exist\n" docker-run-import
	@printf "$(pretty_command): run the tests inside docker, build the docker image with tests if it does not exist\n" docker-run-tests

default: clean-all $(VENV_NAME) install
all-editable: clean-all $(VENV_NAME) install-all-editable

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

install: install-tomato install-mcr 

install-all: PIP_INST_EXTRA:=$(PIP_INST_ALL)
install-all: install-tomato install-mcr 

install-all-editable: PIP_INST_FLAG:=$(PIP_INST_EDIT)
install-all-editable: install-all

install-tomato: $(VENV_NAME)
	source $(VENV_NAME)/bin/activate ; \
	pip install --upgrade pip ; \
	if [ "$(PIP_INST_EXTRA)" = "" ]; then \
        python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .; \
	else \
	    python -m pip $(PIP_FLAG) install $(PIP_INST_FLAG) .[$(PIP_INST_EXTRA)]; \
    fi

install-tomato-$(PIP_INST_DEV): PIP_INST_EXTRA:=$(PIP_INST_DEV)
install-tomato-$(PIP_INST_DEV): install-tomato

install-tomato-$(PIP_INST_DEMO): PIP_INST_EXTRA:=$(PIP_INST_DEMO)
install-tomato-$(PIP_INST_DEMO): install-tomato

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

docker-build:
	docker build . -t $(DOCKER_TAG):$(DOCKER_VER)

docker-build-test: docker-build
	docker build . \
		-f $(DOCKER_TEST_FILE) \
		-t $(DOCKER_TEST_TAG):$(DOCKER_TEST_VER); \

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


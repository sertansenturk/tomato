.PHONY: purge \
	clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin \
	docker-build docker-build-test docker-run-import docker-run-tests \
	install

VENV_INTERP = python3.6
VENV_NAME ?= venv

# PIP_DEV = development
# PIP_DEMO = demo
# PIP_ALL = $(PIP_DEV), $(PIP_DEMO)

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_TEST_TAG = $(DOCKER_TAG)-test
DOCKER_TEST_VER = $(DOCKER_VER)
DOCKER_TEST_FILE = docker/tests/Dockerfile

HELP_PADDING = 18
help:
	@printf "===== Cleanup =====\n"
	@printf "clean             : remove all build, test, coverage and Python artifacts\n"
	@printf "clean-all, purge  : remove all (see: clean), plus virtualenv, and tomato binaries. (virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\")\n"
	@printf "clean-build       : remove build artifacts\n"
	@printf "clean-pyc         : remove Python file artifacts\n"
	@printf "clean-test        : remove test artifacts\n"
	@printf "%-$(HELP_PADDING)s: remove Python virtualenv folder. (virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\")\n" clean-$(VENV_NAME)
	@printf "clean-bin         : remove tomato binaries\n"
	@printf "===== Python ======\n"
	@printf "%-$(HELP_PADDING)s: create a virtualenv. (virtualenv name: \"VENV_NAME ?= $(VENV_NAME)\", Python interpreter: \"VENV_INTERP = $(VENV_INTERP)\")\n" $(VENV_NAME)
	@printf "===== Docker ======\n"
	@printf "docker-build      : build docker image. (tag: \"DOCKER_TAG = $(DOCKER_TAG)\", version: \"DOCKER_VER = $(DOCKER_VER)\")\n"
	@printf "docker-build-test : build a docker image with tests. (tag: \"DOCKER_TEST_TAG = $(DOCKER_TEST_TAG)\", version: \"DOCKER_TEST_VER = $(DOCKER_TEST_VER)\")\n"
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

# isort:
# 	sh -c "isort --skip-glob=.tox --recursive . "

# lint:
# 	flake8 --exclude=.tox

# black:
# 	black --line-length 79 ./

# test: clean-pyc
# 	py.test --verbose --color=yes $(TEST_PATH)

# install: 
# 	. $(VENV_NAME)/bin/activate ; \
# 	pip install --upgrade pip ; \
# 	if [ "${${PIP_EXTRA}})" = "" ]; then \
#         python -m pip install -e .; \
# 	else \
# 	    python -m pip install -e .[$(PIP_EXTRA)] ; \
#     fi

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

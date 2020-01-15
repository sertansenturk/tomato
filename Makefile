.PHONY: purge \
	clean clean-pyc clean-build clean-test clean-$(VENV_NAME) clean-bin \
	docker-build docker-build-test docker-run-import docker-run-tests

VENV_PY_VER = 3.6
VENV_NAME = env

DOCKER_TAG = sertansenturk/tomato
DOCKER_VER = latest
DOCKER_TEST_TAG = $(DOCKER_TAG)-test
DOCKER_TEST_VER = $(DOCKER_VER)
DOCKER_TEST_FILE = docker/tests/Dockerfile

help:
	@echo "===== Cleanup ====="
	@echo "purge             : remove all (see: clean), plus the virtualenv and tomato binaries"
	@echo "clean             : remove all build, test, coverage and Python artifacts"
	@echo "clean-build       : remove build artifacts"
	@echo "clean-pyc         : remove Python file artifacts"
	@echo "clean-test        : remove test artifacts"
	@echo "clean-env         : remove Python virtualenv folder"
	@echo "clean-bin         : remove tomato binaries downloaded during setup"
	@echo "===== Python ====="
	@echo "env               : create a virtualenv (by default) called env"
	@echo "===== Docker ====="
	@echo "docker-build      : build docker image"
	@echo "docker-build-test : build a docker image with tests included"
	@echo "docker-run-import : run the docker image with a dummy analyzer import"
	@echo "docker-run-tests  : run the docker image the tests"

purge: clean-pyc clean-build clean-test clean-VENV_NAME clean-bin

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
	python3 -m virtualenv -p python$(VENV_PY_VER) $(VENV_NAME)

# isort:
# 	sh -c "isort --skip-glob=.tox --recursive . "

# lint:
# 	flake8 --exclude=.tox

# black:
# 	black --line-length 79 ./

# test: clean-pyc
# 	py.test --verbose --color=yes $(TEST_PATH)

# pip-install-development:
# 	pip install --upgrade pip
# 	python -m pip install -e .[development]

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
			"import tomato.symbolic.symbtrconverter; import tomato.joint.completeanalyzer"

docker-run-tests: docker-build-test
	docker run \
		$(DOCKER_TEST_TAG):$(DOCKER_TEST_VER) \
		python3 -m pytest tests

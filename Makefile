clean-dir:
	rm -rf env dist build tomato.egg-info tomato/bin/phraseSeg tomato/bin/extractTonicTempoTuning tomato/bin/alignAudioScore tomato/bin/MusikiToMusicXml

create-virtualenv:
	virtualenv -p python3.6 env

pip-install-development:
	pip install --upgrade pip
	python -m pip install -e .[development] -v

build-docker-image:
	docker build . -t sertansenturk/tomato:latest

docker-test-import:
	make build-docker-image && \
	docker run sertansenturk/tomato python3 -c \
        "import tomato.symbolic.symbtrconverter; import tomato.joint.completeanalyzer"

docker-run-tests:
	make build-docker-image && \
    docker build . -f docker/tests/Dockerfile.smoke -t sertansenturk/tomato-smoke:latest && \
    docker run sertansenturk/tomato-smoke python3 -m pytest tests

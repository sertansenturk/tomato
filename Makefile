clean-dir:
	rm -rf env dist build tomato.egg-info tomato/bin/phraseSeg tomato/bin/extractTonicTempoTuning tomato/bin/alignAudioScore tomato/bin/MusikiToMusicXml

create-virtualenv:
	virtualenv -p python3.6 env

pip-install-development:
	python -m pip install -e .[development] -v

install-to-new-virtualenv:
	deactivate && \ 
	rm -rf env && \
	make create-virtualenv && \
	source env/bin/activate && \
	make pip-install-development

build-docker-image:
	docker build . -t sertansenturk/tomato:latest

docker-test-import:
	make build-docker-image && \
	docker run sertansenturk/tomato python3 -c \
        "import tomato.symbolic.symbtrconverter; import tomato.joint.completeanalyzer"

docker-run-tests:
	make docker && \
    docker build . -f docker/tests/Dockerfile.smoke -t sertansenturk/tomato-smoke:latest && \
    docker run sertansenturk/tomato-smoke python3 -m pytest tests

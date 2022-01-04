SHELL := bash

.PHONY: check clean reformat install run dist

all: install

check:
	scripts/check-code.sh

reformat:
	scripts/format-code.sh

install:
	scripts/create-venv.sh

run:
	bin/coqui-stt --model-dir models/stt-english-mycroft

dist:
	python3 setup.py sdist

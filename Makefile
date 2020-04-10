.SILENT:

SHELL := /bin/bash

MP3SUM_PY2 := printf '  py2: '; python  ./mp3sum/__main__.py --no-colours -qr
MP3SUM_PY3 := printf '  py3: '; python3 ./mp3sum/__main__.py --no-colours -qr

default: build

build:
	./setup.py build

dist:
	./setup.py bdist

install:
	./setup.py install

test:
	echo 'tests/cases/0 (pass):'
	$(MP3SUM_PY2) ./tests/cases/0 2>&1; (( $$? == 0 ))
	$(MP3SUM_PY3) ./tests/cases/0 2>&1; (( $$? == 0 ))

	echo 'tests/cases/2 (skip):'
	$(MP3SUM_PY2) ./tests/cases/2 2>&1; (( $$? == 2 ))
	$(MP3SUM_PY3) ./tests/cases/2 2>&1; (( $$? == 2 ))

	echo 'tests/cases/4 (fail):'
	$(MP3SUM_PY2) ./tests/cases/4 2>&1; (( $$? == 4 ))
	$(MP3SUM_PY3) ./tests/cases/4 2>&1; (( $$? == 4 ))

	echo 'tests/cases/8 (fail):'
	$(MP3SUM_PY2) ./tests/cases/8 2>&1; (( $$? == 8 ))
	$(MP3SUM_PY3) ./tests/cases/8 2>&1; (( $$? == 8 ))

	echo 'OK!'

clean:
	./setup.py clean > /dev/null 2>&1 || true
	rm -rf ./build/ ./dist/ ./*.egg-info/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

.PHONY: default build dist install clean


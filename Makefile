all: setup test

.PHONY: requirements.txt test

setup:
	python3 -m venv ./
	. ./bin/activate
	pip install -r requirements.txt

run:
	. ./bin/activate
	python3 src/main.py --help
	deactivate

test:
	. ./bin/activate
	pytest ./test/
	deactivate

clean:
	. ./bin/activate
	rm -rf .pytest_cache
	rm -rf __pycache__
	deactivate

build:
	docker build --tag kube-rotator:1.0 .

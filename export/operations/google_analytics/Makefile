docker:
	docker build --platform linux/arm64 --tag operations-google-analytics-export .

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501 main.py

pull_request: install install_dev docker lint fmt test

test:
	python -m pytest -s -vv .

build:
	docker build --platform=linux/arm64 -t operations-google-analytics-export .

push:
	aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 454671348950.dkr.ecr.ca-central-1.amazonaws.com
	docker tag operations-google-analytics-export:latest 454671348950.dkr.ecr.ca-central-1.amazonaws.com/operations-google-analytics-export:latest
	docker push 454671348950.dkr.ecr.ca-central-1.amazonaws.com/operations-google-analytics-export:latest

.PHONY: \
	docker \
	fmt \
	install \
	install_dev \
	lint \
	pull_request \
	test \
	build \
	push
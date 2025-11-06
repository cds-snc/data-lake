.PHONY: test build push

test:
	python -m pytest main_test.py -v

build:
	docker build --platform=linux/arm64 -t platform-google-analytics-export .

push:
	aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 454671348950.dkr.ecr.ca-central-1.amazonaws.com
	docker tag platform-google-analytics-export:latest 454671348950.dkr.ecr.ca-central-1.amazonaws.com/platform-google-analytics-export:latest
	docker push 454671348950.dkr.ecr.ca-central-1.amazonaws.com/platform-google-analytics-export:latest

install:
	pip install -r requirements_dev.txt
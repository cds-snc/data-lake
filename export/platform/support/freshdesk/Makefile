docker:
	docker build --platform linux/arm64 --tag platform-support-freshdesk-export .
 
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

.PHONY: \
	docker \
	fmt \
	install	\
	install_dev \
	lint \
	pull_request \
	test
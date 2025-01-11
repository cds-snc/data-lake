.PHONY: build

build:
	docker build --platform linux/amd64 --tag platform-support-freshdesk-export .
 
fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501 main.py

test:
	python -m pytest -s -vv .

.PHONY: \
	build \
	fmt \
	install	\
	install_dev \
	lint \
	test
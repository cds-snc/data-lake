default:
	python process_data.py

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501,E402 *.py

pull_request: install install_dev fmt lint test

test:
	python -m pytest -s -vv .

.PHONY: \
	fmt \
	install	\
	install_dev \
	lint \
	pull_request \
	test
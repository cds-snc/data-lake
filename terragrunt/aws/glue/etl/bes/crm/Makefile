fmt:
	black . $(ARGS)

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501 *.py

pull_request: install_dev fmt lint

.PHONY: \
	fmt \
	install_dev \
	lint \
	pull_request
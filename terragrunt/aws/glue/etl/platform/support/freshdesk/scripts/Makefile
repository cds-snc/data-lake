default:
	python process_ticket_extract.py

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501 *.py

test:
	python -m pytest -s -vv .

.PHONY: \
	fmt \
	install	\
	install_dev \
	lint \
	test
fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install_dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 --ignore=E501,W503 notification_enriched.py notification_enriched_test.py

pull_request: install install_dev lint fmt test

test:
	python -m pytest -s -vv notification_enriched_test.py

clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/

.PHONY: \
	fmt \
	install \
	install_dev \
	lint \
	pull_request \
	test \
	clean

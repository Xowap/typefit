PYTHON_BIN ?= poetry run python
ENV ?= pypitest

format:
	$(PYTHON_BIN) -m monoformat .

%.txt: %.in
	$(PYTHON_BIN) -m piptools compile --generate-hashes $<

test: export PYTHONPATH=$(realpath example)

test:
	$(PYTHON_BIN) -m pytest tests

build:
	poetry install
	cd docs && poetry run make html
	poetry run pip list --format=freeze | grep -v typefit > requirements.txt

publish:
	poetry publish --build

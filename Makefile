PYTHON_BIN ?= poetry run python
ENV ?= pypitest

format: isort black

black:
	$(PYTHON_BIN) -m black --target-version py38 --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' .

isort:
	$(PYTHON_BIN) -m isort src
	$(PYTHON_BIN) -m isort tests

%.txt: %.in
	$(PYTHON_BIN) -m piptools compile --generate-hashes $<

test: export PYTHONPATH=$(realpath example)

test:
	$(PYTHON_BIN) -m pytest tests

build:
	poetry install
	cd docs && poetry run make html
	poetry run pip list --format=freeze | grep -v typefit > requirements.txt

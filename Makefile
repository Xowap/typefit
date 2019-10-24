PYTHON_BIN ?= python
ENV ?= pypitest

format: isort black

black:
	'$(PYTHON_BIN)' -m black --target-version py38 --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' .

isort:
	'$(PYTHON_BIN)' -m isort -rc src
	'$(PYTHON_BIN)' -m isort -rc tests

%.txt: %.in
	'$(PYTHON_BIN)' -m piptools compile --generate-hashes $<

test: export PYTHONPATH=$(realpath example)

test:
	poetry run pytest tests

build:
	poetry install -E api -E dates
	cd docs && poetry run make html
	pip freeze | grep -v egg=typefit > requirements.txt

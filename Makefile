PYTHON_BIN ?= poetry run python
ENV ?= pypitest

format:
	$(PYTHON_BIN) -m monoformat .

%.txt: %.in
	$(PYTHON_BIN) -m piptools compile --generate-hashes $<

test: export PYTHONPATH=$(realpath example)

test:
	$(PYTHON_BIN) -m pytest tests

check_release:
ifndef VERSION
	$(error VERSION is undefined)
endif

release: check_release
	git flow release start $(VERSION)
	sed -i 's/^version =.*/version = "$(VERSION)"/' pyproject.toml
	git add pyproject.toml
	git commit -m "Bump version to $(VERSION)"
	git flow release finish -m "Release $(VERSION)" $(VERSION) > /dev/null

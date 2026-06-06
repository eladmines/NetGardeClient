.PHONY: install run help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make install   Create venv and install netgarde-wg (Python)"
	@echo "  make run ARGS='--config my.conf'   Run client (usually needs sudo)"

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PIP) install .

run: install
	sudo $(PY) -m netgarde_wg $(ARGS)

.PHONY: install run build-mac help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make install        Create venv and install netgarde-wg (Python)"
	@echo "  make run ARGS='...' Run client via Python (usually needs sudo)"
	@echo "  make build-mac      Build dist/netgarde-wg + dist/wireguard-go (macOS only)"

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PIP) install .

run: install
	sudo $(PY) -m netgarde_wg $(ARGS)

build-mac:
	bash scripts/build-macos.sh

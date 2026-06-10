.PHONY: install install-gui install-dev test run run-gui build-mac build-mac-app help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make install        Create venv and install trustedge-wg (Python)"
	@echo "  make install-gui    Install with macOS menu bar GUI (rumps)"
	@echo "  make install-dev    Install package with dev deps (pytest, PyInstaller)"
	@echo "  make test           Run pytest"
	@echo "  make run ARGS='...' Run CLI via Python (usually needs sudo)"
	@echo "  make run-gui        Launch menu bar app (dev, via Python)"
	@echo "  make build-mac      Build dist/trustedge-wg + dist/TrustEdge.app"
	@echo "  make build-mac-app  Alias for build-mac"

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install .

install-gui: install
	$(PIP) install ".[gui]"

install-dev: install
	$(PIP) install ".[dev]"

test: install-dev
	$(PY) -m pytest -q

run: install
	sudo $(PY) -m trustedge_wg $(ARGS)

run-gui: install-gui
	$(PY) -m trustedge_wg.gui.app

build-mac:
	bash scripts/build-macos.sh

build-mac-app: build-mac

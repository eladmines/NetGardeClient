.PHONY: install install-gui run run-gui build-mac build-mac-app help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make install        Create venv and install netgarde-wg (Python)"
	@echo "  make install-gui    Install with macOS menu bar GUI (rumps)"
	@echo "  make run ARGS='...' Run CLI via Python (usually needs sudo)"
	@echo "  make run-gui        Launch menu bar app (dev, via Python)"
	@echo "  make build-mac      Build dist/netgarde-wg + dist/NetGarde.app"
	@echo "  make build-mac-app  Alias for build-mac"

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install .

install-gui: install
	$(PIP) install ".[gui]"

run: install
	sudo $(PY) -m netgarde_wg $(ARGS)

run-gui: install-gui
	$(PY) -m netgarde_wg.gui.app

build-mac:
	bash scripts/build-macos.sh

build-mac-app: build-mac

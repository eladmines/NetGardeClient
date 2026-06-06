.PHONY: install install-gui run run-gui build-mac help

VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make install        Create venv and install netgarde-wg (Python)"
	@echo "  make install-gui    Install with macOS menu bar GUI (rumps)"
	@echo "  make run ARGS='...' Run CLI via Python (usually needs sudo)"
	@echo "  make run-gui        Launch macOS menu bar app"
	@echo "  make build-mac      Build dist/netgarde-wg + dist/wireguard-go (macOS only)"

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

SHELL=/bin/bash

all: help

help:
	@echo HELP
	@echo
	@echo install
	@echo meshtastic
	@echo


.PHONY: install

install:
	if [[ ! -d venv ]]; then python3 -m venv venv; fi
	. venv/bin/activate && pip install --upgrade -r requirements.txt
	. venv/bin/activate && meshtastic --version

meshtastic:
	. venv/bin/activate && meshtastic

meshtastic-config:
	. venv/bin/activate && meshtastic --export-config

meshtastic-info:
	. venv/bin/activate && meshtastic --info

meshtastic-metadata:
	. venv/bin/activate && meshtastic --device-metadata


SHELL=/bin/bash

all: help

help:
	@echo HELP
	@echo
	@echo install
	@echo
	@echo meshtastic
	@echo meshtastic-config
	@echo meshtastic-info
	@echo meshtastic-metadata
	@echo
	@echo config-download
	@echo config-upload
	@echo
	@echo flash-bootloader-download
	@echo flash-bootloader-upload
	@echo flash-firmware-download
	@echo flash-firmware-upload
	@echo



.PHONY: install

install:
	if [[ ! -d venv ]]; then python3 -m venv venv; fi
	. venv/bin/activate && pip install --upgrade -r requirements.txt
	. venv/bin/activate && meshtastic --version
	. venv/bin/activate && python3 -m pip install --pre -U git+https://github.com/makerdiary/uf2utils.git@main



.PHONY: meshtastic meshtastic-config meshtastic-info meshtastic-metadata
meshtastic:
	. venv/bin/activate && meshtastic

meshtastic-config:
	. venv/bin/activate && meshtastic --export-config

meshtastic-info:
	. venv/bin/activate && meshtastic --info

meshtastic-metadata:
	. venv/bin/activate && meshtastic --device-metadata



.PHONY: config-download config-upload

config-download:
	. venv/bin/activate && ./meshtastic_download_setup.py

config-upload:
	. venv/bin/activate && ./meshtastic_upload_setup.py




DEV=/dev/ttyACM0

BOOTLOADER=t1000_e_bootloader-0.9.1-5-g488711a_s140_7.3.0.zip

.PHONY: flash-bootloader-download flash-bootloader-upload flash-firmware-upload

$(BOOTLOADER):
	wget https://files.seeedstudio.com/wiki/SenseCAP/lorahub/$(BOOTLOADER)

flash-bootloader-download: $(BOOTLOADER)

flash-bootloader-upload: flash-bootloader-download
	adafruit-nrfutil --verbose dfu serial --package $(BOOTLOADER) -p $(DEV) --singlebank --touch 1200

flash-firmware-upload:
	cd ~ && if [[ ! -d "meshfirmware" ]]; then git clone https://github.com/mikecarper/meshfirmware.git; fi
	cd ~/meshfirmware && git pull && chmod +x mtfirmware.sh && ./mtfirmware.sh

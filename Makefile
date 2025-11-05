SHELL=/bin/bash

all: help

help:
	@echo HELP
	@echo
	@echo meshtastic
	@echo meshtastic-config
	@echo meshtastic-info
	@echo meshtastic-metadata
	@echo
	@echo flash-bootloader-download
	@echo flash-bootloader-upload
	@echo flash-firmware-download
	@echo flash-firmware-upload
	@echo
	@echo install
	@echo


.PHONY: install

install:
	if [[ ! -d venv ]]; then python3 -m venv venv; fi
	. venv/bin/activate && pip install --upgrade -r requirements.txt
	. venv/bin/activate && meshtastic --version
	. venv/bin/activate && python3 -m pip install --pre -U git+https://github.com/makerdiary/uf2utils.git@main

meshtastic:
	. venv/bin/activate && meshtastic

meshtastic-config:
	. venv/bin/activate && meshtastic --export-config

meshtastic-info:
	. venv/bin/activate && meshtastic --info

meshtastic-metadata:
	. venv/bin/activate && meshtastic --device-metadata





.PHONY: flash-bootloader-download flash-bootloader-upload

DEV=/dev/ttyACM0

BOOTLOADER=t1000_e_bootloader-0.9.1-5-g488711a_s140_7.3.0.zip
FIRMWARE_VER=2.6.11.60ec05e
FIRMWARE_FILE=firmware-tracker-t1000-e-$(FIRMWARE_VER).uf2
FIRMWARE_URL=https://raw.githubusercontent.com/meshtastic/meshtastic.github.io/master/firmware-$(FIRMWARE_VER)/$(FIRMWARE_FILE)


$(BOOTLOADER):
	wget https://files.seeedstudio.com/wiki/SenseCAP/lorahub/$(BOOTLOADER)

flash-bootloader-download: $(BOOTLOADER)

flash-bootloader-upload: flash-bootloader-download
	adafruit-nrfutil --verbose dfu serial --package $(BOOTLOADER) -p $(DEV) --singlebank --touch 1200

$(FIRMWARE_FILE):
	wget $(FIRMWARE_URL)

flash-firmware-download: $(FIRMWARE_FILE)

nfutil:
	wget -O nfutil https://'files.nordicsemi.com/ui/api/v1/download?repoKey=swtools&path=external/nrfutil/executables/x86_64-unknown-linux-gnu/nrfutil&isNativeBrowsing=false'
	chmod +x nfutil

# https://wiki.makerdiary.com/nrf52840-mdk-usb-dongle/programming/uf2boot/#installing-uf2-converter
flash-firmware-upload: flash-firmware-download nfutil
	meshtastic --enter-dfu
	#adafruit-nrfutil --verbose dfu serial --package $(FIRMWARE_FILE) -p $(DEV) --singlebank --touch 1200
	#uf2conv --info                   $(FIRMWARE_FILE)
	#uf2conv --deploy --device $(DEV) $(FIRMWARE_FILE)

# meshtastic-py-config

## Install

```
sudo apt install make
sudo apt install python3.13-venv
sudo apt install unzip

make install
```

## Bootloader

<https://wiki.seeedstudio.com/sensecap_t1000_e/#flash-the-bootloader>

<https://files.seeedstudio.com/wiki/SenseCAP/lorahub/t1000_e_bootloader-0.9.1-5-g488711a_s140_7.3.0.zip>

## Firmware

<https://flasher.meshtastic.org/>

- Select board
- Select version
- Select Upload
- Get Link

<https://raw.githubusercontent.com/meshtastic/meshtastic.github.io/master/firmware-2.6.11.60ec05e/firmware-tracker-t1000-e-2.6.11.60ec05e.uf2>

Enter DFU

	meshtastic --enter-dfu

Run UF2Utils

<https://wiki.makerdiary.com/nrf52840-mdk-usb-dongle/programming/uf2boot/#installing-uf2-converter>

<https://www.nordicsemi.com/Products/Development-tools/nrf-util>


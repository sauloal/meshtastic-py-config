#!/usr/bin/env python

import json
import yaml

from pathlib import Path

import subprocess

CONFIG_DIR="configs/"

INFO  = 8
DEBUG = 9

def get_info(verbosity: int = 0):
	info = subprocess.Popen("meshtastic --info", shell=True, stdout=subprocess.PIPE).stdout.read().decode()
	assert info
	info_lines = info.split("\n")
	assert len(info_lines) > 0
	assert info_lines[0] == 'Connected to radio'
	#print(info_lines)

	owner                     = None
	my_info_json              = None
	metadata_json             = None
	nodes_json                = None
	nodes_json_m              = None
	preferences_json          = None
	preferences_json_m        = None
	module_preferences_json   = None
	module_preferences_json_m = None
	channels                  = None
	channels_m                = None
	primary_channel           = None
	all_channels              = None

	for ln, line in enumerate(info_lines):
		if verbosity >= DEBUG: print(ln, f"'{line}'")

		if   owner is None and line.startswith('Owner: '):
			owner = line[8:]
			if verbosity >= INFO: print(f"  OWNER '{owner}'")
		elif my_info_json is None and line.startswith('My info: '):
			my_info_json = line[9:]
			if verbosity >= INFO: print(f"  INFO '{my_info_json}'")
		elif metadata_json is None and line.startswith('Metadata: '):
			metadata_json = line[10:]
			if verbosity >= INFO: print(f"  METADATA '{metadata_json}'")
		elif nodes_json is None and line.startswith('Nodes in mesh: '):
			nodes_json   = line[15:] + "\n"
			nodes_json_m = True
			if verbosity >= DEBUG: print(f"  NODES '{nodes_json}'")
		elif nodes_json_m:
			nodes_json += line + "\n"
			if line == "}":
				nodes_json_m = False
				if verbosity >= INFO: print(f"  NODES '{nodes_json}'")
		elif preferences_json is None and line.startswith('Preferences: '):
			preferences_json   = line[13:] + "\n"
			preferences_json_m = True
			if verbosity >= DEBUG: print(f"  PREFERENCES '{preferences_json}'")
		elif preferences_json_m:
			preferences_json += line + "\n"
			if line == "}":
				preferences_json_m = False
				if verbosity >= INFO: print(f"  PREFERENCES '{preferences_json}'")
		elif module_preferences_json is None and line.startswith('Module preferences: '):
			module_preferences_json   = line[20:] + "\n"
			module_preferences_json_m = True
			if verbosity >= DEBUG: print(f"  MODULE PREFERENCES '{module_preferences_json}'")
		elif module_preferences_json_m:
			module_preferences_json += line + "\n"
			if line == "}":
				module_preferences_json_m = False
				if verbosity >= INFO: print(f"  MODULE PREFERENCES '{preferences_json}'")
		elif channels is None and line.startswith('Channels:'):
			channels   = []
			channels_m = True
			if verbosity >= DEBUG: print(f"  CHANNELS '{channels}'")
		elif channels_m:
			if line != "":
				channels.append( line.strip() )
			else:
				channels_m = False
				if verbosity >= INFO: print(f"  CHANNELS '{channels}'")
		elif   primary_channel is None and line.startswith('Primary channel URL: '):
			primary_channel = line[21:]
			if verbosity >= INFO: print(f"  PRIMARY CHANNEL '{primary_channel}'")
		elif   all_channels is None and line.startswith('Complete URL (includes all channels): '):
			all_channels = line[38:]
			if verbosity >= INFO: print(f"  ALL CHANNELS '{all_channels}'")

	my_info            = json.loads(my_info_json)
	metadata           = json.loads(metadata_json)
	nodes              = json.loads(nodes_json)
	preferences        = json.loads(preferences_json)
	module_preferences = json.loads(module_preferences_json)

	my_info["myNodeId"] = my_info["myNodeNum"].to_bytes(4, byteorder='big').hex()
	# node id  !8f6ff8be  = (2406480062).to_bytes(4, byteorder='big').hex()
	# node num 2406480062 = int('8f6ff8be', 16)
	# mac addr dc:54:8f:6f:f8:be

	# CHANNELS '[
	#'Index 0: PRIMARY psk=secret { "psk": "59ELzvnD1WQ0c30CNK/FZuEIZjjDy8jXpYHxVlvq4lE=", "name": "LongFastAfl", "moduleSettings": { "positionPrecision": 32, "isClientMuted": false }, "channelNum": 0, "id": 0, "uplinkEnabled": false, "downlinkEnabled": false }',
	#'Index 1: SECONDARY psk=default { "psk": "AQ==", "moduleSettings": { "positionPrecision": 14, "isClientMuted": false }, "channelNum": 0, "name": "", "id": 0, "uplinkEnabled": false, "downlinkEnabled": false }']'
	channels_info = []
	for ch_idx, ch in enumerate(channels):
		ch_cols       = ch.split(":", maxsplit=1)
		ch_index      = int(ch_cols[0].split(" ")[1]) # Index 0 1
		ch_vals       = ch_cols[1].strip()
		ch_vals_parts = ch_vals.split(" ", maxsplit=2)
		ch_type       = ch_vals_parts[0] # PRIMARY SECONDARY
		ch_psk        = ch_vals_parts[1].split("=")[1] # secret default
		ch_json       = ch_vals_parts[2]
		ch_info       = json.loads(ch_json)
		channels_info.append({
			"index": ch_index,
			"type":  ch_type,
			"psk":   ch_psk,
			"info":  ch_info
		})


	info = {
		"owner":              owner,
		"my_info":            my_info,
		"metadata":           metadata,
		"nodes":              nodes,
		"preferences":        preferences,
		"module_preferences": module_preferences,
		"channels":           channels_info,
		"primary_channel":    primary_channel,
		"all_channels":       all_channels
	}

	node_id     = info["my_info"]["myNodeId"]

	return node_id, info

def save_info(info, outfile: str|Path):
	outfile = Path(outfile)

	if outfile.exists():
		outfile.unlink()

	print(f"Exporting info   to {outfile}")

	with open(outfile, "wt") as fhd:
		yaml.safe_dump(info, fhd)

	assert outfile.exists()


def save_config(outfile: str|Path):
	outfile = Path(outfile)

	if outfile.exists():
		outfile.unlink()

	print(f"Exporting config to {outfile}")

	res     = subprocess.Popen(f"meshtastic --export-config {outfile}", shell=True, stdout=subprocess.PIPE).stdout.read().decode()

	print(res)

	assert outfile.exists(), f"config file was not created: {outfile}"

def set_config(outfile: str|Path):
	outfile = Path(outfile)

	assert outfile.exists()

	print(f"Setting config from {outfile}")

	res     = subprocess.Popen(f"meshtastic --configure {outfile}", shell=True, stdout=subprocess.PIPE).stdout.read().decode()

	print(res)

def main():
	config_dir = Path(CONFIG_DIR)

	if not config_dir.exists():
		config_dir.mkdir()

	node_id, info = get_info()

	#print("INFO", json.dumps(info, indent=1, sort_keys=True))

	outfile     = Path(f"{config_dir}/{node_id}.yaml")
	outfile_cfg = Path(f"{config_dir}/{node_id}.cfg.yaml")

	save_info(  info, outfile)
	save_config(outfile_cfg)

if __name__ == "__main__":
	main()


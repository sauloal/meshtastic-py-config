#!/usr/bin/env python

import io
import sys
import json
import yaml

from pathlib import Path

import subprocess

import meshtastic_download_setup

DRY_RUN      = True
DEBUG        = False

CONFIG_DIR   = meshtastic_download_setup.CONFIG_DIR
TEMPLATE_DIR = "templates/"
SECRET_DIR   = "secrets/"

EXCLUDE_KEYS = {
	"channel_url": None,
	"location": None,
	"module_config": {
		"ambientLighting": None
	}
}

def merge_dict(d1, d2):
	if isinstance(d2, dict):
		assert isinstance(d1, dict)
		for k2, v2 in d2.items():
			if k2 in d1:
				if   isinstance(v2, list):
					raise NotImplementedError()
				elif isinstance(v2, (int, float, str)):
					d1[k2] = v2
				elif  isinstance(v2, dict):
					d1[k2] = merge_dict(d1[k2], v2)
				else:
					raise NotImplementedError()
			else:
				d1[k2] = v2
	else:
		raise NotImplementedError()

	return d1

def _exclude_keys(d1, d2):
	for k2, v2 in d2.items():
		if v2 is None:
			if k2 in d1:
				del d1[k2]
		else:
			if k2 in d1:
				d1[k2] = _exclude_keys(d1[k2], d2[k2])
	return d1

def _get_config(node_id: str, folder: str|Path, exclude_keys: dict|None=None):
	assert folder.exists()
	assert folder.is_dir()

	data = None
	for file in (folder/"_all.yaml", folder/f"{node_id}.cfg.yaml"):
		if file.exists():
			with file.open("rt") as fhd:
				cfg  = yaml.safe_load(fhd)
				data = cfg if data is None else merge_dict(data, cfg)
	if exclude_keys:
		data = _exclude_keys(data, exclude_keys)

	return data

def _debug_merge(data, name):
	for k,v in data.items():
		if isinstance(v, dict):
			data[k] = _debug_merge(v, name)
		else:
			data[k] = f"{name}-{v}"
	return data

def calc_dict_diff(d1, d2, depth=0):
	if d1 is None: d1 = {}
	if d2 is None: d2 = {}

	if isinstance(d1, dict):
		assert isinstance(d2, dict)
		k1s  = list(d1.keys())
		k2s  = list(d2.keys())
		keys = sorted( set( k1s + k2s ) )
		for k in keys:
			v1 = d1.get(k, None)
			v2 = d2.get(k, None)
			if isinstance(v1, dict) or isinstance(v2, dict):
				print(f"{' '*depth}{k}:")
				calc_dict_diff(v1, v2, depth=depth+1)
			else:
				if   v1 is None and v2 is None:
					pass
				elif v1 != v2:
					print(f"{' '*depth}{k}: {v1} <=> {v2}")
				else:
					print(f"{' '*depth}{k}: {v1} === {v2}")

def get_config(node_id: str, config_dir: str|Path = CONFIG_DIR, debug: bool=False, exclude_keys: dict|None=None):
	config_dir   = Path(config_dir)
	data         = _get_config(node_id, config_dir, exclude_keys=exclude_keys)
	if debug:
		data = debug_merge(data, "config")
	return data

def get_templates(node_id: str, template_dir: str|Path = TEMPLATE_DIR, debug: bool=False):
	template_dir = Path(template_dir)
	data         = _get_config(node_id, template_dir)
	if debug:
		data = debug_merge(data, "template")
	return data

def get_secrets(node_id: str,secret_dir: str|Path = SECRET_DIR, debug: bool=False):
	secret_dir   = Path(secret_dir)
	data         = _get_config(node_id, secret_dir)
	if debug:
		data = debug_merge(data, "secret")
	return data

def main():
	dry_run       = DRY_RUN
	debug         = DEBUG

	try:
		dry_run = sys.argv[1].lower() not in "1,y,yes,t,true".split(",")
	except IndexError:
		pass

	if dry_run:
		print("DRY RUN")

	template_dir    = Path(TEMPLATE_DIR)
	secret_dir      = Path(SECRET_DIR)

	node_id, info   = meshtastic_download_setup.get_info()

	#print("INFO")
	#yaml.safe_dump(info, sys.stdout)

	config_dir      = Path(CONFIG_DIR)
	assert config_dir.exists()
	assert config_dir.is_dir()
	outfile_cfg     = Path(f"{config_dir}/{node_id}.cfg.yaml")
	meshtastic_download_setup.save_config(outfile_cfg)

	print("="*50)
	print("CONFIG")
	print("="*50)
	config          = get_config(   node_id, config_dir,   debug=debug, exclude_keys=EXCLUDE_KEYS)
	yaml.safe_dump(config  , sys.stdout)

	print("="*50)
	print("TEMPLATE")
	print("="*50)
	template        = get_templates(node_id, template_dir, debug=debug)
	yaml.safe_dump(template, sys.stdout)

	print("="*50)
	print("SECRET")
	print("="*50)
	secret          = get_secrets(  node_id, secret_dir,   debug=debug)
	yaml.safe_dump(secret  , sys.stdout)

	data            = None
	if debug:
		data    = config
		data    = merge_dict(data, template)
	else:
		data    = template

	data            = merge_dict(data, secret)

	print("="*50)
	print("DATA")
	print("="*50)
	yaml.safe_dump(data, sys.stdout)

	fi       = io.StringIO()
	fo       = io.StringIO()
	yaml.safe_dump(config, fi)
	yaml.safe_dump(data  , fo)
	config_y = fi.getvalue()
	data_y   = fo.getvalue()
	config_l = config_y.split("\n")
	data_l   = data_y.split("\n")

	if config_y == data_y:
		print(f"CONFIG ALREADY UP-TO-DATE")
		return

	print("="*50)
	print(f"CONFIG DIFFER")
	print("="*50)
	print("-"*50)
	print("config_y")
	print(config_y)
	print("-"*50)
	print("data_y")
	print(data_y)
	print("-"*50)
	print("diff")
	calc_dict_diff(config, data)
	print("-"*50)
	for row_num in range(max(len(config_l), len(data_l))):
		try:
			config_row = config_l[row_num]
		except IndexError:
			config_row = None
		try:
			data_row   = data_l[row_num]
		except IndexError:
			data_row   = None
		print(f"{str(config_row == data_row):5s}  {str(config_row):45s} {str(data_row):45s}")
	print("="*50)

	outfile_cfg   = Path(f"{config_dir}/{node_id}.upd.yaml")
	with outfile_cfg.open("wt") as fhd:
		fhd.write(data_y)

	if dry_run:
		print(" dry run")
	else:
		print(" uploading")
		meshtastic_download_setup.set_config(outfile_cfg)

	print(f"deleting {outfile_cfg}")
	outfile_cfg.unlink()

if __name__ == "__main__":
	main()


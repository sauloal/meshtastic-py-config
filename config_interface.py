from copy import deepcopy
import os
import yaml

import meshtastic
import meshtastic.serial_interface

from config_proto import *

CONFIG_FOLDER = "configs"
CONFIG_ALL    = f"{CONFIG_FOLDER}/all.yaml"
CONFIG_CREDS  = f"{CONFIG_FOLDER}/creds.yaml"


class Interface:
    def __init__(self, verbose=False):
        self.verbose = verbose
        # https://meshtastic.org/docs/software/python/python-cli

        # https://meshtastic.org/docs/software/python/python-using-library

        # By default will try to find a meshtastic device,
        # otherwise provide a device path like /dev/ttyUSB0
        self._interface = meshtastic.serial_interface.SerialInterface()
        # or something like this
        # interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/cu.usbmodem53230050571')

        self._node = self._interface.getNode('^local')
        # print(dir(ourNode))

        self._channels = self._node.channels

        self.get_info()
        self.get_nodes()
        self.read_config()

    @property
    def node(self): return self._node
    @property
    def channels(self): return self._channels
    @property
    def myInfo(self): return self._myInfo
    @property
    def nodes(self): return self._nodes
    @property
    def interface(self): return self._interface
    @property
    def curr_node(self): return self._curr_node
    @property
    def id(self): return self._id
    @property
    def node_num(self): return self._node_num
    @property
    def shortName(self): return self._shortName
    @property
    def longName(self): return self._longName
    @property
    def hwModel(self): return self._hwModel
    @property
    def macaddr(self): return self._macaddr
    @property
    def firmware_version(self): return self._firmware_version
    @property
    def config_node(self): return f"{CONFIG_FOLDER}/{self.node_num}.yaml"
    @property
    def config(self): return self._config
    @property
    def localConfig(self): return self.node.localConfig
    @property
    def moduleConfig(self): return self.node.moduleConfig

    def get_info(self):
        assert self._interface.myInfo

        self._myInfo = self._interface.myInfo

        if self.verbose:
            print(f'myInfo::{self.myInfo}')

        self._node_num         = self.myInfo.my_node_num
        self._firmware_version = self.myInfo.firmware_version
        # print(f'firmware_version::{interface.myInfo.firmware_version}')
        """
            myInfo::
                my_node_num: 621134896
                max_channels: 8
                firmware_version: "1.3.40.e87ecc2-d"
                reboot_count: 4
                bitrate: 74.3412857
                message_timeout_msec: 300000
                min_app_version: 20300
                has_wifi: true
                channel_utilization: 3.895
                air_util_tx: 1.04583335
                firmware_version:1.3.40.e87ecc2-d
        """

    def get_nodes(self):
        assert self._interface.nodes

        self._nodes     = self._interface.nodes.values()
        self._curr_node = None

        for n in self._nodes:
            if n['num'] == self._node_num:
                if self.verbose:
                    print("CURRENT", n)
                self._curr_node = n
                # print(n['user']['hwModel'])
            else:
                if self.verbose:
                    print("OTHER", n)

        """
            CURRENT {'num': 621134896, 'user': {'id': '!2505c430', 'longName': 'Meshtastic c430', 'shortName': 'c430', 'macaddr': 'WL8lBcQw', 'hwModel': 'TBEAM'}, 'position': {},             'lastHeard': 1663440764, 'deviceMetrics': {'batteryLevel': 100, 'voltage': 4.129, 'channelUtilization': 5.66 , 'airUtilTx': 0.98933333}}
            OTHER   {'num': 621049908, 'user': {'id': '!25047834', 'longName': 'Meshtastic 7834', 'shortName': '7834', 'macaddr': 'WL8lBHg0', 'hwModel': 'TBEAM'},                 'snr': 8.5, 'lastHeard': 1663440356, 'deviceMetrics': {'batteryLevel':  33, 'voltage': 3.699, 'channelUtilization': 3.895, 'airUtilTx': 0.6704444}}
            OTHER   {'num': 621110596, 'user': {'id': '!25056544', 'longName': 'Meshtastic 6544', 'shortName': '6544', 'macaddr': 'WL8lBWVE', 'hwModel': 'TBEAM'},                 'snr': 3.5, 'lastHeard': 1663440560, 'deviceMetrics': {'batteryLevel':  16, 'voltage': 3.6  ,                              'airUtilTx': 1.0018611}}
        """

        assert self._curr_node

        self._id        = self._curr_node["user"]["id"]
        self._shortName = self._curr_node["user"]["shortName"]
        self._longName  = self._curr_node["user"]["longName"]
        self._hwModel   = self._curr_node["user"]["hwModel"]
        self._macaddr   = self._curr_node["user"]["macaddr"]

        if self.verbose:
            print(f"node_num          {self._node_num}")
            print(f"id                {self._id}")
            print(f"shortName         {self._shortName}")
            print(f"longName          {self._longName}")
            print(f"hwModel           {self._hwModel}")
            print(f"macaddr           {self._macaddr}")
            print(f"firmware_version  {self._firmware_version}")

    def read_config(self):
        CONFIG_NODE   = self.config_node

        config_all    = None
        config_creds  = None
        config_node   = None


        if os.path.exists(CONFIG_ALL):
            with open(CONFIG_ALL, "rt") as fhd:
                config_all = yaml.safe_load(fhd)
            if self.verbose:
                print("CONFIG_ALL\n", yaml.safe_dump(config_all))


        if os.path.exists(CONFIG_CREDS):
            with open(CONFIG_CREDS, "rt") as fhd:
                config_creds = yaml.safe_load(fhd)
            if self.verbose:
                print("CONFIG_CREDS\n", yaml.safe_dump(config_creds))


        if os.path.exists(CONFIG_NODE):
            with open(CONFIG_NODE, "rt") as fhd:
                config_node = yaml.safe_load(fhd)
            if self.verbose:
                print("CONFIG_NODE\n", yaml.safe_dump(config_node))


        configs = [c for c in (config_all, config_creds, config_node) if c is not None]
        assert len(configs) > 0
        if   len(configs) == 1:
            config_merged = configs[0]
        elif len(configs) == 2:
            config_merged = merge_configs(configs[0], configs[1])
        else:
            config_merged = configs[0]
            for c in configs[1:]:
                config_merged = merge_configs(config_merged, c)
        if self.verbose:
            print("CONFIG_MERGED\n", yaml.safe_dump(config_merged))

        self._config        = Config.from_dict_and_device(deepcopy(config_merged), self)
        self._config_local  = Config.from_dict(deepcopy(config_merged))
        self._config_device = Config.from_device(self)

        print()
        # print("self._config       ", self._config     .to_template())
        print("self._config       ", self._config     .to_json())
        print("self._config       ", self._config     .to_dict())

        print()
        # print("self._config_local ", self._config_local.to_template())
        print("self._config_local ", self._config_local.to_json())
        print("self._config_local ", self._config_local.to_dict())

        print()
        # print("self._config_device", self._config_device.to_template())
        print("self._config_device", self._config_device.to_json())
        print("self._config_device", self._config_device.to_dict())

        print()
        if self.verbose:
            print("self._config", self._config)

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "node_num": self.node_num,
            "shortName": self.shortName,
            "longName": self.longName,
            "hwModel": self.hwModel,
            "macaddr": self.macaddr,
            "firmware_version": self.firmware_version,
            "config_node": self.config_node,
        }, indent=1, sort_keys=True)

    def apply_changes(self):
        self.config.apply_changes(self)



def merge_configs(dicta, dictb):
    res = {}
    if dictb is None:
        res = dicta
    elif dicta is None:
        res = dictb
    else:
        if isinstance(dicta, dict) and isinstance(dictb, dict):
            allkeys = list(set(list(dicta.keys()) + list(dictb.keys())))

            for k in allkeys:
                vala = dicta.get(k, None)
                valb = dictb.get(k, None)
                if vala is None:
                    res[k] = valb
                elif valb is None:
                    res[k] = vala
                else:
                    res[k] = merge_configs(vala, valb)
        else:
            assert False, f"{dicta} {dictb}"
    return res

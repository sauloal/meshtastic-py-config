import yaml

import meshtastic
import meshtastic.serial_interface
from meshtastic.util import pskToString, stripnl
from google.protobuf.json_format import MessageToJson

# https://meshtastic.org/docs/software/python/python-cli

# https://meshtastic.org/docs/software/python/python-using-library

# By default will try to find a meshtastic device,
# otherwise provide a device path like /dev/ttyUSB0
interface = meshtastic.serial_interface.SerialInterface()
# or something like this
# interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/cu.usbmodem53230050571')


ourNode = interface.getNode('^local')
# print(dir(ourNode))

if interface.myInfo:
    print(f'myInfo::{interface.myInfo}')
    print(f'firmware_version::{interface.myInfo.firmware_version}')
    """
        myInfo:my_node_num: 621134896
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

if interface.nodes:
    for n in interface.nodes.values():
        if n['num'] == interface.myInfo.my_node_num:
            print("CURRENT", n)
            # print(n['user']['hwModel'])
        else:
            print("OTHER", n)
    """
        CURRENT {'num': 621134896, 'user': {'id': '!2505c430', 'longName': 'Meshtastic c430', 'shortName': 'c430', 'macaddr': 'WL8lBcQw', 'hwModel': 'TBEAM'}, 'position': {},             'lastHeard': 1663440764, 'deviceMetrics': {'batteryLevel': 100, 'voltage': 4.129, 'channelUtilization': 5.66 , 'airUtilTx': 0.98933333}}
        OTHER   {'num': 621049908, 'user': {'id': '!25047834', 'longName': 'Meshtastic 7834', 'shortName': '7834', 'macaddr': 'WL8lBHg0', 'hwModel': 'TBEAM'},                 'snr': 8.5, 'lastHeard': 1663440356, 'deviceMetrics': {'batteryLevel':  33, 'voltage': 3.699, 'channelUtilization': 3.895, 'airUtilTx': 0.6704444}}
        OTHER   {'num': 621110596, 'user': {'id': '!25056544', 'longName': 'Meshtastic 6544', 'shortName': '6544', 'macaddr': 'WL8lBWVE', 'hwModel': 'TBEAM'},                 'snr': 3.5, 'lastHeard': 1663440560, 'deviceMetrics': {'batteryLevel':  16, 'voltage': 3.6  ,                              'airUtilTx': 1.0018611}}
    """

print("channels::", ourNode.channels, type(ourNode.channels))

for c in ourNode.channels:
  print("c", c)
  print("c.settings", c.settings)
  print("stripnl", stripnl(MessageToJson(c.settings)))
  print("PSK", pskToString(c.settings.psk))
  # channel_pb2.Channel.Role.Name(c.role)
# print("show channels::", ourNode.showChannels())
# deleteChannel
# exitSimulator
# getChannelByChannelIndex
# getChannelByName
# getDisabledChannel
# partialChannels
# writeChannel



"""
channels [settings {
  psk: "\001"
}
role: PRIMARY
, index: 1
settings {
}
, index: 2
, index: 3
, index: 4
, index: 5
, index: 6
, index: 7
]
Channels:
  PRIMARY psk=default { "psk": "AQ==" }

Primary channel URL: https://www.meshtastic.org/e/#CgMiAQESAjgD

show channels None
"""

print("nodeNum::", ourNode.nodeNum, type(ourNode.nodeNum))
"""
nodeNum 621134896

firmware_version: 1.3.40.e87ecc2-d
device_state_version: 16
"""

metadata = None
def onRequestGetMetadata(p):
    """Handle the response packet for requesting device metadata getMetadata()"""
    # logging.debug(f'onRequestGetMetadata() p:{p}')
    c = p["decoded"]["admin"]["raw"].get_device_metadata_response
    ourNode._timeout.reset()  # We made foreward progress
    # logging.debug(f"Received metadata {stripnl(c)}")
    # print(f"\nfirmware_version: {c.firmware_version}")
    # print(f"device_state_version: {c.device_state_version}")
    global metadata
    metadata = c

def onResponseRequestCannedMessagePluginMessageMessages(p):
    """Handle the response packet for requesting canned message plugin message part 1"""
    # logging.debug(f'onResponseRequestCannedMessagePluginMessageMessages() p:{p}')
    errorFound = False
    if "routing" in p["decoded"]:
        if p["decoded"]["routing"]["errorReason"] != "NONE":
            errorFound = True
            print(f'Error on response: {p["decoded"]["routing"]["errorReason"]}')
    if errorFound is False:
        if "decoded" in p:
            if "admin" in p["decoded"]:
                if "raw" in p["decoded"]["admin"]:
                    ourNode.cannedPluginMessageMessages = p["decoded"]["admin"]["raw"].get_canned_message_module_messages_response
                    # logging.debug(f'self.cannedPluginMessageMessages:{self.cannedPluginMessageMessages}')
                    ourNode.gotResponse = True

# ourNode.onRequestGetMetadataOrig = ourNode.onRequestGetMetadata
ourNode.onRequestGetMetadata = onRequestGetMetadata
# print(ourNode.onRequestGetMetadataOrig)
# print(ourNode.onRequestGetMetadata)

print("getMetadata::", ourNode.getMetadata())
from time import sleep
while metadata is None:
    sleep(1)
print("metadata", metadata, type(metadata))
"""
getMetadata to: 621134896
decoded {
  portnum: ADMIN_APP
  payload: "\240\003\001"
  want_response: true
}
id: 1753137143
hop_limit: 3
want_ack: true
"""

print("getURL::", ourNode.getURL())
# setURL
"""
getURL https://www.meshtastic.org/e/#CgMiAQESAjgD
canned_plugin_message:
"""

print("get_canned_message::", ourNode.get_canned_message(), type(ourNode.get_canned_message()))
print("cannedPluginMessageMessages::",ourNode.cannedPluginMessageMessages, type(ourNode.cannedPluginMessageMessages))

"""
get_canned_message::
Preferences: { "device": { "ntpServer": "0.pool.ntp.org" }, "position": { "positionFlags": 3 }, "power": { "lsSecs": 300 }, "wifi": {}, "display": {}, "lora": { "region": "EU868" }, "bluetooth": { "enabled": true, "fixedPin": 123456 } }

Module preferences: { "mqtt": {}, "serial": {}, "externalNotification": {}, "rangeTest": {}, "telemetry": {}, "cannedMessage": {} }

Channels:
  PRIMARY psk=default { "psk": "AQ==" }

Primary channel URL: https://www.meshtastic.org/e/#CgMiAQESAjgD
"""
# set_canned_message
# cannedPluginMessage
# cannedPluginMessageMessages

# ourNode.setOwner

print("showInfo::", ourNode.showInfo())
# print("iface::", ourNode.iface)

print("localConfig::", ourNode.localConfig, type(ourNode.localConfig))
"""
localConfig:: device {
  ntp_server: "0.pool.ntp.org"
}
position {
  position_flags: 3
}
power {
  ls_secs: 300
}
wifi {
}
display {
}
lora {
  region: EU868
}
bluetooth {
  enabled: true
  fixed_pin: 123456
}
"""

print("moduleConfig::", ourNode.moduleConfig, type(ourNode.moduleConfig))
"""
moduleConfig:: mqtt {
}
serial {
}
external_notification {
}
range_test {
}
telemetry {
}
canned_message {
}
"""

print("requestConfig::", ourNode.requestConfig())
# print("waitForConfig::", ourNode.waitForConfig())
# waitForConfig
# writeConfig
print("self.channels", ourNode.channels)
"""
requestConfig:: None
"""

"""
gotResponse
noProto
onRequestGetMetadata
onResponseRequestCannedMessagePluginMessageMessages
onResponseRequestChannel
reboot
shutdown
turnOffEncryptionOnPrimaryChannel
"""

# print(f'Our node preferences:{ourNode.radioConfig.preferences}')

# update a value
# print('Changing a preference...')
# ourNode.radioConfig.preferences.gps_update_interval = 60

# print(f'Our node preferences now:{ourNode.radioConfig.preferences}')
# ourNode.writeConfig()

# setOwner(self, long_name=None, short_name=None, is_licensed=False)

print(dir(ourNode.localConfig))
# print("ourNode.localConfig.ListFields", ourNode.localConfig.ListFields())

print("ourNode.localConfig.device", ourNode.localConfig.device, ourNode.localConfig.device.ListFields())
print("ourNode.localConfig.position", ourNode.localConfig.position, ourNode.localConfig.position.ListFields())
print("ourNode.localConfig.power", ourNode.localConfig.power, ourNode.localConfig.power.ListFields())
# print("ourNode.localConfig.network", ourNode.localConfig.network)
# print("ourNode.localConfig.display", ourNode.localConfig.display)
print("ourNode.localConfig.lora", ourNode.localConfig.lora, ourNode.localConfig.lora.ListFields())
print("ourNode.localConfig.bluetooth", ourNode.localConfig.bluetooth, ourNode.localConfig.bluetooth.ListFields())

print(dir(ourNode.moduleConfig))

ourNode.moduleConfig.mqtt
ourNode.moduleConfig.serial
ourNode.moduleConfig.external_notification
ourNode.moduleConfig.store_forward
ourNode.moduleConfig.range_test
ourNode.moduleConfig.telemetry
ourNode.moduleConfig.canned_message


interface.close()



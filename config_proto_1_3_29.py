from enum import Enum, Flag as EnumFlag

from dataclasses import dataclass
import typing

from meshtastic.util import pskToString, fromPSK

from config_proto_tools import *

__verion__         = "1.3.29"
__protobuf_ver__   = "https://github.com/meshtastic/Meshtastic-protobufs/tree/a72983993ccd9c2dabb1ef9e17b2fe79bd94d671"
__meshtastic_ver__ = "https://github.com/meshtastic/Meshtastic-python/tree/1.3.29"



@dataclass
class Config(DataClassSerializer):
    node: "NodeConfig" = Empty(None)
    config: "LocalConfig" = Empty(None)
    modules: "ModuleConfig" = Empty(None)

    def apply_changes(self, interface, dry_run=True):
        node               = interface.node

        has_update_node    = self.node   .apply_changes(interface                   , dry_run=dry_run)
        has_update_config  = self.config .apply_changes(node     , node.localConfig , dry_run=dry_run)
        has_update_modules = self.modules.apply_changes(node     , node.moduleConfig, dry_run=dry_run)
        
        # TODO: enable wrinting config
        if has_update_config or has_update_modules:
            print(" writing config")
            if dry_run:
                print("  DRY RUN")
            else:
                # interface.node.writeConfig()
                pass

    def load_device(self, interface):
        print(" load_device")

        node               = interface.node

        self.node   .load_device(interface)
        self.config .load_device(node.localConfig)
        self.modules.load_device(node.moduleConfig)



@dataclass
class NodeConfig(DataClassSerializer):
    owner      : str = Empty(None)
    owner_short: str = Empty(None)
    channels   : typing.List[typing.Dict[str,str]] = Empty(None) #TODO: get default channels

    def apply_changes(self, interface, dry_run=True):
        shortName          = interface.shortName
        longName           = interface.longName
        update_owner = False
        
        if self.owner is not None and isinstance(self.owner, Empty) and self.owner and longName is not None:
            print("  updating owner long")
            update_owner = True

        if self.owner_short is not None and isinstance(self.owner_short, Empty) and self.owner_short and shortName is not None:
            print("  updating owner short")
            update_owner = True

        if update_owner:
            print(f"updating owner owner_short {self.owner_short} shortName {shortName} owner {self.owner} longName {longName}")
            if dry_run:
                print("  DRY RUN")
            else:
                interface.node.setOwner(long_name=longName, short_name=shortName)


        has_any_channel_update = False
        for channel_num, channel_info in enumerate(self.channels):
            channel_name   = channel_info["name"]
            channel_psk    = channel_info["psk"]
            channel_data   = interface.channels[channel_num]
            channel_psk_v  = pskToString(channel_data.settings.psk)
            channel_name_v = channel_data.settings.name
            # TODO: delete channel
            print(f"channel_num {channel_num} channel_name {channel_name} channel_psk {channel_psk} ({channel_psk_v}) channel_data {channel_data}")
            has_channel_update = False
            if channel_psk != channel_psk_v:
                print("  updating channel PSK")
                psk = fromPSK(channel_psk)
                channel_data.settings.psk = psk.encode() if isinstance(psk, str) else psk
                has_channel_update = True
            if channel_name != channel_name_v:
                print("  updating channel Name")
                channel_data.settings.name = channel_name_v
                has_channel_update = True
            if has_channel_update:
                has_any_channel_update = True
                if dry_run:
                    print("  DRY RUN")
                else:
                    print("  writting channel")
                    interface.node.writeChannel(channel_num)

                # setOwner(self, long_name=None, short_name=None, is_licensed=False)
                # ourNode.channels
                # deleteChannel(self, channelIndex)
                # self.channels[0].settings.psk = meshtastic.util.fromPSK("none")
                #     meshtastic.util.fromPSK(valstr)
                #     if valstr == "random":
                #     elif valstr == "none":
                #     elif valstr == "default":
                #     elif valstr.startswith("simple"):
                # pskToString
                # c.settings.name
                # getChannelByChannelIndex(channelIndex)
                # max_channel = 7
                pass

        return has_any_channel_update or update_owner

    def load_device(self, interface):
        pass


@dataclass
class LocalConfig(DataClassSerializer):
    """
    https://github.com/meshtastic/Meshtastic-protobufs/blob/a72983993ccd9c2dabb1ef9e17b2fe79bd94d671/config.proto
    * Configuration
    """

    @dataclass
    class DeviceConfig(DataClassSerializer, AttributeChanger):
        """
        * Defines the device's role on the Mesh network
        """

        class Role(Enum):
            CLIENT = 0
            """
            * Client device role
            """
            
            CLIENT_MUTE = 1
            """
            * Client Mute device role
            *   Same as a client except packets will not hop over this node, does not contribute to routing packets for mesh.
            """
            
            ROUTER = 2
            """
            * Router device role.
            *   Mesh packets will prefer to be routed over this node. This node will not be used by client apps. 
            *   The wifi/ble radios and the oled screen will be put to sleep.
            """
            
            ROUTER_CLIENT = 3
            """
            * Router Client device role
            *   Mesh packets will prefer to be routed over this node. The Router Client can be used as both a Router and an app connected Client.
            """

        role: Role = Empty(0)
        """
        * Sets the role of node
        """

        serial_disabled: bool = Empty(False)
        """
        * Disabling this will disable the SerialConsole by not initilizing the StreamAPI
        """

        factory_reset: bool = Empty(False)
        """
        * This setting is never saved to disk, but if set, all device settings will be returned to factory defaults.
        """

        debug_log_enabled: bool = Empty(False)
        """
        * By default we turn off logging as soon as an API client connects (to keep shared serial link quiet).
        * Set this to true to leave the debug log outputting even when API is active.
        """

        ntp_server: str = Empty("0.pool.ntp.org")
        """
        * NTP server to use if WiFi is conneced, defaults to `0.pool.ntp.org`
        """


    @dataclass
    class PositionConfig(DataClassSerializer, AttributeChanger):
        """
        * Bit field of boolean configuration options, indicating which optional
        *   fields to include when assembling POSITION messages
        * Longitude and latitude are always included (also time if GPS-synced)
        * NOTE: the more fields are included, the larger the message will be -
        *   leading to longer airtime and a higher risk of packet loss
        """
        class PositionFlags(EnumFlag):
            POS_UNDEFINED = 0x0000
            """
            * Required for compilation
            """
          
            POS_ALTITUDE  = 0x0001
            """
            * Include an altitude value (if available)
            """
          
            POS_ALT_MSL   = 0x0002
            """
            * Altitude value is MSL
            """
          
            POS_GEO_SEP   = 0x0004
            """
            * Include geoidal separation
            """
          
            POS_DOP       = 0x0008
            """
            * Include the DOP value ; PDOP used by default, see below
            """
          
            POS_HVDOP     = 0x0010
            """
            * If POS_DOP set, send separate HDOP / VDOP values instead of PDOP
            """
          
            POS_SATINVIEW = 0x0020
            """
            * Include number of "satellites in view"
            """
          
            POS_SEQ_NOS   = 0x0040
            """
            * Include a sequence number incremented per packet
            """
          
            POS_TIMESTAMP = 0x0080
            """
            * Include positional timestamp (from GPS solution)
            """
            
            POS_HEADING   = 0x0100
            """
            * Include positional heading
            * Intended for use with vehicle not walking speeds
            * walking speeds are likely to be error prone like the compass
            """
            
            POS_SPEED     = 0x0200
            """
            * Include positional speed
            * Intended for use with vehicle not walking speeds
            * walking speeds are likely to be error prone like the compass
            """

        position_broadcast_secs: int = Empty(0)
        """
        * We should send our position this often (but only if it has changed significantly)
        * Defaults to 15 minutes
        """

        position_broadcast_smart_disabled: bool = Empty(False)
        """
        * Adaptive position braoadcast, which is now the default.
        """

        fixed_position: bool = Empty(False)
        """
        * If set, this node is at a fixed position.
        * We will generate GPS position updates at the regular interval, but use whatever the last lat/lon/alt we have for the node.
        * The lat/lon/alt can be set by an internal GPS or with the help of the app.
        """

        gps_disabled: bool = Empty(False)
        """
        * Is GPS enabled for this node?
        """

        gps_update_interval: int = Empty(0)
        """
        * How often should we try to get GPS position (in seconds)
        * or zero for the default of once every 30 seconds
        * or a very large value (maxint) to update only once at boot.
        """

        gps_attempt_time: int = Empty(0)
        """
        * How long should we try to get our position during each gps_update_interval attempt?  (in seconds)
        * Or if zero, use the default of 30 seconds.
        * If we don't get a new gps fix in that time, the gps will be put into sleep until  the next gps_update_rate
        * window.
        """
    
        position_flags: PositionFlags = Empty(3)
        """
        * Bit field of boolean configuration options for POSITION messages
        * (bitwise OR of PositionFlags)
        """


    @dataclass
    class PowerConfig(DataClassSerializer, AttributeChanger):
        """
        * Power Config
        * See [Power Config](/docs/settings/config/power) for additional power config details.
        """

        class ChargeCurrent(Enum):
            MAUnset =  0
            MA100   =  1
            MA190   =  2
            MA280   =  3
            MA360   =  4
            MA450   =  5
            MA550   =  6
            MA630   =  7
            MA700   =  8
            MA780   =  9
            MA880   = 10
            MA960   = 11
            MA1000  = 12
            MA1080  = 13
            MA1160  = 14
            MA1240  = 15
            MA1320  = 16

        charge_current: ChargeCurrent = Empty(0)
        """
        * Sets the current of the battery charger
        * TBEAM 1.1 Only
        """
        
        is_power_saving: bool = Empty(False)
        """
        * If set, we are powered from a low-current source (i.e. solar), so even if it looks like we have power flowing in
        * we should try to minimize power consumption as much as possible.
        * YOU DO NOT NEED TO SET THIS IF YOU'VE set is_router (it is implied in that case).
        * Advanced Option
        """

        on_battery_shutdown_after_secs: int = Empty(0)
        """
        * If non-zero, the device will fully power off this many seconds after external power is removed.
        """

        adc_multiplier_override: float = Empty(0)
        """
        * Ratio of voltage divider for battery pin eg. 3.20 (R1=100k, R2=220k)
        * Overrides the ADC_MULTIPLIER defined in variant for battery voltage calculation.
        * Should be set to floating point value between 2 and 4
        * Fixes issues on Heltec v2
        """

        wait_bluetooth_secs: int = Empty(0)
        """
        * Wait Bluetooth Seconds
        * The number of seconds for to wait before turning off BLE in No Bluetooth states
        * 0 for default of 1 minute
        """

        mesh_sds_timeout_secs: int = Empty(0)
        """
        * Mesh Super Deep Sleep Timeout Seconds
        * While in Light Sleep if this value is exceeded we will lower into super deep sleep 
        * for sds_secs (default 1 year) or a button press
        * 0 for default of two hours, MAXUINT for disabled
        """
    
        sds_secs: int = Empty(0)
        """
        * Super Deep Sleep Seconds
        * While in Light Sleep if mesh_sds_timeout_secs is exceeded we will lower into super deep sleep
        * for this value (default 1 year) or a button press
        * 0 for default of one year
        """
    
        ls_secs: int = Empty(300)
        """
        * Light Sleep Seconds
        * In light sleep the CPU is suspended, LoRa radio is on, BLE is off an GPS is on
        * ESP32 Only
        * 0 for default of 300
        """
    
        min_wake_secs: int = Empty(0)
        """
        * Minimum Wake Seconds
        * While in light sleep when we receive packets on the LoRa radio we will wake and handle them and stay awake in no BLE mode for this value
        * 0 for default of 10 seconds
        """


    @dataclass
    class WiFiConfig(DataClassSerializer, AttributeChanger):
        class WiFiMode(Enum):
          Client = 0
          """
          * This mode is used to connect to an external WiFi network
          """

          AccessPoint = 1
          """
          * In this mode the node will operate as an AP (and DHCP server)
          """

          AccessPointHidden = 2
          """
          * If set, the node AP will broadcast as a hidden SSID
          """

        enabled: bool = Empty(False)
        """
        * Enable WiFi (disables Bluetooth)
        """

        mode: WiFiMode = Empty(0)
        """
        * If set, this node will try to join the specified wifi network and
        * acquire an address via DHCP
        """

        ssid: str = Empty('')
        """
        * If set, this node will try to join the specified wifi network and
        * acquire an address via DHCP
        """

        psk: str = Empty('')
        """
        * If set, will be use to authenticate to the named wifi
        """


    @dataclass
    class DisplayConfig(DataClassSerializer, AttributeChanger):
        """
        * How the GPS coordinates are displayed on the OLED screen.
        """
        class GpsCoordinateFormat(Enum):
            GpsFormatDec = 0
            """
            * GPS coordinates are displayed in the normal decimal degrees format:
            * DD.DDDDDD DDD.DDDDDD
            """

            GpsFormatDMS = 1
            """
            * GPS coordinates are displayed in the degrees minutes seconds format:
            * DD°MM'SS"C DDD°MM'SS"C, where C is the compass point representing the locations quadrant
            """

            GpsFormatUTM = 2
            """
            * Universal Transverse Mercator format:
            * ZZB EEEEEE NNNNNNN, where Z is zone, B is band, E is easting, N is northing
            """

            GpsFormatMGRS = 3
            """
            * Military Grid Reference System format:
            * ZZB CD EEEEE NNNNN, where Z is zone, B is band, C is the east 100k square, D is the north 100k square,
            * E is easting, N is northing
            """

            GpsFormatOLC = 4
            """
            * Open Location Code (aka Plus Codes).
            """

            GpsFormatOSGR = 5
            """
            * Ordnance Survey Grid Reference (the National Grid System of the UK).
            * Format: AB EEEEE NNNNN, where A is the east 100k square, B is the north 100k square,
            * E is the easting, N is the northing
            """

        screen_on_secs: int = Empty(0)
        """
        * Number of seconds the screen stays on after pressing the user button or receiving a message
        * 0 for default of one minute MAXUINT for always on
        """

        gps_format: GpsCoordinateFormat = Empty(0)
        """
        * How the GPS coordinates are formatted on the OLED screen.
        """

        auto_screen_carousel_secs: int = Empty(0)
        """
        * Automatically toggles to the next page on the screen like a carousel, based the specified interval in seconds.
        * Potentially useful for devices without user buttons.
        """
        
        compass_north_top: bool = Empty(False)
        """
        * If this is set, the displayed compass will always point north. if unset, the old behaviour 
        * (top of display is heading direction) is used.
        """


    @dataclass
    class LoRaConfig(DataClassSerializer, AttributeChanger):
        class RegionCode(Enum):
            Unset = 0
            """
            * Region is not set
            """

            US = 1
            """
            * United States
            """

            EU433 = 2
            """
            * European Union 433mhz
            """

            EU868 = 3
            """
            * European Union 433mhz
            """

            CN = 4
            """
            * China
            """

            JP = 5
            """
            * Japan
            """

            ANZ = 6
            """
            * Australia / New Zealand
            """

            KR = 7
            """
            * Korea
            """

            TW = 8
            """
            * Taiwan
            """

            RU = 9
            """
            * Russia
            """

            IN = 10
            """
            * India
            """

            NZ865 = 11
            """
            * New Zealand 865mhz
            """

            TH = 12
            """
            * Thailand
            """

        class ModemPreset(Enum):
            """
            * Standard predefined channel settings
            * Note: these mappings must match ModemPreset Choice in the device code.
            """

            LongFast = 0
            """
            * Long Range - Fast
            """

            LongSlow = 1
            """
            * Long Range - Slow
            """

            VLongSlow = 2
            """
            * Very Long Range - Slow
            """

            MedSlow = 3
            """
            * Medium Range - Slow
            """

            MedFast = 4
            """
            * Medium Range - Fast
            """

            ShortSlow = 5
            """
            * Short Range - Slow
            """

            ShortFast = 6
            """
            * Short Range - Fast
            """

        modem_preset: ModemPreset = Empty(0)
        """
        * Either modem_config or bandwidth/spreading/coding will be specified - NOT BOTH.
        * As a heuristic: If bandwidth is specified, do not use modem_config.
        * Because protobufs take ZERO space when the value is zero this works out nicely.
        * This value is replaced by bandwidth/spread_factor/coding_rate.
        * If you'd like to experiment with other options add them to MeshRadio.cpp in the device code.
        """

        bandwidth: int = Empty(0)
        """
        * Bandwidth in MHz
        * Certain bandwidth numbers are 'special' and will be converted to the
        * appropriate floating point value: 31 -> 31.25MHz
        """

        spread_factor: int = Empty(0)
        """
        * A number from 7 to 12.
        * Indicates number of chirps per symbol as 1<<spread_factor.
        """

        coding_rate: int = Empty(0)
        """
        * The denominator of the coding rate.
        * ie for 4/8, the value is 8. 5/8 the value is 5.
        """

        frequency_offset: float = Empty(0.0)
        """
        * This parameter is for advanced users with advanced test equipment, we do not recommend most users use it.
        * A frequency offset that is added to to the calculated band center frequency.
        * Used to correct for crystal calibration errors.
        """

        region: RegionCode = Empty(0)
        """
        * The region code for the radio (US, CN, EU433, etc...)
        """

        hop_limit: int = Empty(0)
        """
        * Maximum number of hops. This can't be greater than 7.
        * Default of 3
        """

        tx_disabled: bool = Empty(False)
        """
        * Disable TX from the LoRa radio. Useful for hot-swapping antennas and other tests.
        * Defaults to false
        """

        tx_power: int = Empty(0)
        """
        * If zero then, use default max legal continuous power (ie. something that won't
        * burn out the radio hardware)
        * In most cases you should use zero here.
        * Units are in dBm.
        """

        ignore_incoming: int = Empty([])
        """
        * For testing it is useful sometimes to force a node to never listen to
        * particular other nodes (simulating radio out of range). All nodenums listed
        * in ignore_incoming will have packets they send droped on receive (by router.cpp)
        """


    @dataclass
    class BluetoothConfig(DataClassSerializer, AttributeChanger):
        class PairingMode(Enum):
            RandomPin = 0
            """
            * Device generates a random pin that will be shown on the screen of the device for pairing
            """

            FixedPin = 1
            """
            * Device requires a specified fixed pin for pairing
            """

            NoPin = 2
            """
            * Device requires no pin for pairing
            """

        enabled: bool = Empty(True)
        """
        * Enable Bluetooth on the device
        """

        mode: PairingMode = Empty(0)
        """
        * Determines the pairing strategy for the device
        """

        fixed_pin: int = Empty(12345)
        """
        * Specified pin for PairingMode.FixedPin
        """

    device   : DeviceConfig    = Empty(None)
    position : PositionConfig  = Empty(None)
    power    : PowerConfig     = Empty(None)
    wifi     : WiFiConfig      = Empty(None)
    display  : DisplayConfig   = Empty(None)
    lora     : LoRaConfig      = Empty(None)
    bluetooth: BluetoothConfig = Empty(None)



@dataclass
class ModuleConfig(DataClassSerializer):
    """
    # https://github.com/meshtastic/Meshtastic-protobufs/blob/a72983993ccd9c2dabb1ef9e17b2fe79bd94d671/module_config.proto
    """

    @dataclass
    class MQTTConfig(DataClassSerializer, AttributeChanger):
        enabled: bool = Empty(False)
        """
        * If a meshtastic node is able to reach the internet it will normally attempt to gateway any channels that are marked as
        * is_uplink_enabled or is_downlink_enabled.
        """

        address: str = Empty('')
        """
        * The server to use for our MQTT global message gateway feature.
        * If not set, the default server will be used
        """

        username: str = Empty('')
        """
        * MQTT username to use (most useful for a custom MQTT server).
        * If using a custom server, this will be honoured even if empty.
        * If using the default server, this will only be honoured if set, otherwise the device will use the default username
        """

        password: str = Empty('')
        """
        * MQTT password to use (most useful for a custom MQTT server).
        * If using a custom server, this will be honoured even if empty.
        * If using the default server, this will only be honoured if set, otherwise the device will use the default password
        """

        encryption_enabled: bool = Empty(False)
        """
        * Whether to send encrypted or decrypted packets to MQTT.
        * This parameter is only honoured if you also set server
        * (the default official mqtt.meshtastic.org server can handle encrypted packets)
        * Decrypted packets may be useful for external systems that want to consume meshtastic packets
        """

        json_enabled: bool = Empty(False)
        """
        * Whether to send / consume json packets on MQTT
        """


    @dataclass
    class SerialConfig(DataClassSerializer, AttributeChanger):
        class Serial_Baud(Enum):
            BAUD_Default =  0
            BAUD_110     =  1
            BAUD_300     =  2
            BAUD_600     =  3
            BAUD_1200    =  4
            BAUD_2400    =  5
            BAUD_4800    =  6
            BAUD_9600    =  7
            BAUD_19200   =  8
            BAUD_38400   =  9
            BAUD_57600   = 10
            BAUD_115200  = 11
            BAUD_230400  = 12
            BAUD_460800  = 13
            BAUD_576000  = 14
            BAUD_921600  = 15

        class Serial_Mode(Enum):
            MODE_Default = 0
            MODE_SIMPLE  = 1
            MODE_PROTO   = 2

        """
        * Preferences for the SerialModule
        """
        enabled: bool = Empty(False)

        echo: bool = Empty(False)

        rxd: int = Empty(0)
        
        txd: int = Empty(0)

        baud: Serial_Baud = Empty(0)

        timeout: int = Empty(0)
    
        mode: Serial_Mode = Empty(0)


    @dataclass
    class ExternalNotificationConfig(DataClassSerializer, AttributeChanger):
        """
        * Preferences for the ExternalNotificationModule
        """
        enabled: bool = Empty(False)

        output_ms: int = Empty(0)

        output: int = Empty(0)

        active: bool = Empty(False)

        alert_message: bool = Empty(False)

        alert_bell: bool = Empty(False)


    @dataclass
    class StoreForwardConfig(DataClassSerializer, AttributeChanger):
        """
        * Enable the Store and Forward Module
        """
        enabled: bool = Empty(False)

        heartbeat: bool = Empty(False)
    
        records: int = Empty(0)

        history_return_max: int = Empty(0)

        history_return_window: int = Empty(0)


    @dataclass
    class RangeTestConfig(DataClassSerializer, AttributeChanger):
        enabled: bool = Empty(False)
        """
        * Enable the Range Test Module
        """

        sender: int = Empty(0)
        """
        * Send out range test messages from this node
        """

        save: bool = Empty(False)
        """
        * Bool value indicating that this node should save a RangeTest.csv file. 
        * ESP32 Only
        """


    @dataclass
    class TelemetryConfig(DataClassSerializer, AttributeChanger):
        device_update_interval: int = Empty(0)
        """
        * Interval in seconds of how often we should try to send our
        * device metrics to the mesh
        """

        environment_update_interval: int = Empty(0)
        """
        * Interval in seconds of how often we should try to send our
        * environment measurements to the mesh
        """

        environment_measurement_enabled: bool = Empty(False)
        """
        * Preferences for the Telemetry Module (Environment)
        * Enable/Disable the telemetry measurement module measurement collection
        """

        environment_screen_enabled: bool = Empty(False)
        """
        * Enable/Disable the telemetry measurement module on-device display
        """

        environment_display_fahrenheit: bool = Empty(False)
        """
        * We'll always read the sensor in Celsius, but sometimes we might want to
        * display the results in Fahrenheit as a "user preference".
        """


    @dataclass
    class CannedMessageConfig(DataClassSerializer, AttributeChanger):
        class InputEventChar(Enum):
            KEY_NONE   =  0
            KEY_UP     = 17
            KEY_DOWN   = 18
            KEY_LEFT   = 19
            KEY_RIGHT  = 20
            KEY_SELECT = 10
            KEY_BACK   = 27
            KEY_CANCEL = 24

        rotary1_enabled: bool = Empty(False)
        """
        * Enable the rotary encoder #1. This is a 'dumb' encoder sending pulses on both A and B pins while rotating.
        """

        inputbroker_pin_a: int = Empty(0)
        """
        * GPIO pin for rotary encoder A port.
        """
    
        inputbroker_pin_b: int = Empty(0)
        """
        * GPIO pin for rotary encoder B port.
        """
    
        inputbroker_pin_press: int = Empty(0)
        """
        * GPIO pin for rotary encoder Press port.
        """
    
        inputbroker_event_cw: InputEventChar = Empty(0)
        """
        * Generate input event on CW of this kind.
        """
    
        inputbroker_event_ccw: InputEventChar = Empty(0)
        """
        * Generate input event on CCW of this kind.
        """
    
        inputbroker_event_press: InputEventChar = Empty(0)
        """
        * Generate input event on Press of this kind.
        """
    
        updown1_enabled: bool = Empty(False)
        """
        * Enable the Up/Down/Select input device. Can be RAK rotary encoder or 3 buttons. Uses the a/b/press definitions from inputbroker.
        """
        
        enabled: bool = Empty(False)
        """
        * Enable/disable CannedMessageModule.
        """
    
        allow_input_source: str = Empty('')
        """
        * Input event origin accepted by the canned message module.
        * Can be e.g. "rotEnc1", "upDownEnc1" or keyword "_any"
        """
    
        send_bell: bool = Empty(False)
        """
        * CannedMessageModule also sends a bell character with the messages.
        * ExternalNotificationModule can benefit from this feature.
        """

    mqtt                 : MQTTConfig                 = Empty(None)
    serial               : SerialConfig               = Empty(None)
    external_notification: ExternalNotificationConfig = Empty(None)
    store_forward        : StoreForwardConfig         = Empty(None)
    range_test           : RangeTestConfig            = Empty(None)
    telemetry            : TelemetryConfig            = Empty(None)
    canned_message       : CannedMessageConfig        = Empty(None)

from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default


import pkg_resources
meshtastic_version = pkg_resources.get_distribution("meshtastic").version
# print(meshtastic_version)


if   meshtastic_version == '1.3.29':
    from config_proto_1_3_29 import *
elif meshtastic_version == '1.4':
    from config_proto_1_4 import *

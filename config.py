import sys

import pkg_resources

from config_proto import *
from config_interface import *

verbose = False
# verbose = True

def get_config():
    meshtastic_version = pkg_resources.get_distribution("meshtastic").version
    print("#", meshtastic_version)

    d = yaml.safe_dump(json.loads(json.dumps(Config.get_empty().to_template())))
    print(d)

def apply_changes():
    interface = Interface(verbose=verbose)

    print("interface", interface)

    # print("interface.config", interface.config)

    # interface.apply_changes()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_config()
    else:
        apply_changes()

import typing
import json
import yaml

import dataclasses
from dataclasses import dataclass

from enum import Enum, Flag as EnumFlag

# @dataclass(repr=False)
class Empty:
    default: typing.Any = None

    def __init__(self, default):
        self.default = default

    def to_json(self):
        return None

    @classmethod
    def to_yaml(cls, dumper, data):
        return None

    def __str__(self):
        return '<Empty>'

    def __repr__(self):
        return '<Empty>'

yaml.add_representer(Empty, lambda dumper, data: None)
yaml.SafeDumper.add_representer(Empty, lambda dumper, data: yaml.representer.SafeRepresenter.represent_str(dumper, "EMPTY"))

def subtract_dicts(local, device, level=0):
    res = {}
    keys = sorted(list(set(list(local.keys()) + list(device.keys()))))
    # print(keys)
    for key in keys:
        # print(f"{'  '*level}{level} subtract_dicts {key}")
        val_local  = local .get(key, None)
        val_device = device.get(key, None)

        # print(f"{'  '*level}{level}   val_local  {key} {val_local}" )
        # print(f"{'  '*level}{level}   val_device {key} {val_device}")

        if val_local == val_device:
            continue

        val = None
        if isinstance(val_local, dict) or isinstance(val_device, dict):
            sub_local  = val_local
            sub_device = val_device

            if not isinstance(sub_local , dict) and sub_local  is None:
                sub_local  = {}
            if not isinstance(sub_device, dict) and sub_device is None:
                sub_device = {}

            val = subtract_dicts(sub_local, sub_device, level=level+1)

        else:
            if val_local is None:
                if val_device is not None:
                    #TOO: Unset
                    continue
            else: # val is not None
                if val_device is None:
                    val = val_local
                else: # device is not None
                    val = val_local

        # print(f"{'  '*level}{level}   val       {key} {val}")

        if val is None:
            continue

        if isinstance(val, dict):
            if not val:
                continue

        res[key] = val

    return res


@dataclass
class DataClassSerializer:
    def dict_factory(self, val: typing.List[typing.Tuple[str, typing.Any]], delete_empty=True):
        data = {k:v for k,v in val}
        if delete_empty:
            data = {k:v for k,v in data.items() if v is not None and not isinstance(v, Empty)}
        return data if data else None

    def to_dict(self):
        data = dataclasses.asdict(self, dict_factory=self.dict_factory)
        return data if data else None

    def to_template(self):
        data = dataclasses.asdict(self, dict_factory=lambda v: self.dict_factory(v, delete_empty=False))
        return data

    def to_json(self):
        return self.to_dict()

    @classmethod
    def get_empty(cls):
        kwargs         = {}
        resolved_hints = typing.get_type_hints(cls)
        for k in dataclasses.fields(cls):
            name  = k.name
            vtype = resolved_hints[name]
            if isinstance(vtype,type) and issubclass(vtype, DataClassSerializer):
                temp = vtype.get_empty().to_template()
                inst = vtype.from_dict(temp)
                # print("  get_empty :: k", k, "name", name, "vtype", vtype, type(vtype), "temp", temp, "inst", inst)
                kwargs[name] = inst
        inst = cls(**kwargs)
        # print("get_empty :: cls   ", cls, dataclasses.is_dataclass(cls))
        # print("get_empty :: kwargs", kwargs)
        # print("get_empty :: inst  ", cls, inst, type(inst), inst.as_template())
        # print()
        return inst

    @classmethod
    def from_dict(cls, kwargs):
        if kwargs is None:
            return None

        resolved_hints = typing.get_type_hints(cls)
        for k in dataclasses.fields(cls):
            name  = k.name
            vtype = resolved_hints[name]
            if name in kwargs:
                if isinstance(vtype, type) and issubclass(vtype, DataClassSerializer):
                    val  = kwargs[k.name]
                    # print("  from_dict :: name", name, "vtype", vtype, type(vtype), "val", val)
                    if val is None:
                        nval = val
                    else:
                        nval = vtype.from_dict(val)
                        # print("    from_dict :: nval", nval)
                    kwargs[name] = nval
        inst = cls(**kwargs)
        # print("    from_dict :: cls   ", cls, dataclasses.is_dataclass(cls))
        # print("    from_dict :: kwargs", kwargs)
        # print("    from_dict :: inst  ", inst, type(inst))
        # print()
        return inst

    @classmethod
    def from_device(cls, interface):
        # print(f"FROM DEVICE {cls}")
        empty     = cls.get_empty()
        # print(f"FROM DEVICE {empty}")
        empty.load_device(interface)
        return empty

    @classmethod
    def from_dict_and_device(cls, config, interface):
        config_local       = cls.from_dict(  config   )
        config_device      = cls.from_device(interface)

        config_local_dict  = config_local .to_dict()
        config_device_dict = config_device.to_dict()

        print("config_local_dict ", config_local_dict)
        print("config_device_dict", config_device_dict)

        config_summary     = subtract_dicts(config_local_dict, config_device_dict)
        print("config_summary    ", config_summary)

        return cls.from_dict(config_summary)

    def apply_changes(self, node, config, dry_run=True):
        # print("  NODE", node, "CONFIG", config)
        for el in dataclasses.fields(self):
            # print("  EL", el)
            el_func = getattr(self, el.name)
            if isinstance(el_func,type) and issubclass(el_func, DataClassSerializer):
                el_val  = getattr(config, el.name)
                # print("     el_func", el_func, "el_val", el_val)
                el_func.apply_changes(node, el_val, dry_run=dry_run)
                # getattr(self, el.name).apply_changes(node, getattr(config, el.name), dry_run=dry_run)

    def load_device(self, config):
        print("CONFIG", config, type(config))
        print("SELF  ", self  , type(self))
        resolved_hints = typing.get_type_hints(self)
        for field in dataclasses.fields(self):
            field_type = resolved_hints[field.name]
            field_val  = getattr(self  , field.name)
            device_val = getattr(config, field.name)
            # print(" FIELD", field.name, field_type, type(field_type), isinstance(field_type,type))
            if isinstance(field_type,type) and issubclass(field_type, DataClassSerializer):
                # print(f"     MOD device_val '{device_val}' field_val '{field_val}'")
                field_val.load_device(device_val)
            else:
                # print(f"     VAL device_val '{device_val}' field_val '{field_val}'")
                if device_val != field_val:
                    if isinstance(field_val, Empty) and field_val.default == device_val:
                        # print(f"       DEFAULT VALUE. skipping")
                        pass
                    else:
                        print(f"       LOADING DEVICE VALUE :: {field.name}: {device_val}")
                        setattr(self, field.name, device_val)

        print()

    def __str__(self):
        return json.dumps(self, indent=1)

    def __repr__(self):
        return str(self)


@dataclass
class AttributeChanger:
    def apply_changes(self, node, config, dry_run=True):
        resolved_hints = typing.get_type_hints(self)
        # print("SELF  ", self, self.__class__)
        # print("CONFIG", config, config.__class__, config.ListFields())
        opts = {}
        for o, v in config.ListFields():
            # print(o.name, v)
            opts[o.name] = v
        # print(opts)

        d = self.as_dict()
        if d is None:
            return None

        has_channel_update = False
        for k, v in d.items():
            var_type = resolved_hints[k]
            # print(f" key {k}")

            if issubclass(var_type, EnumFlag):
                print("SETTING ENUM FLAG ATTRIBUTE", k ,v, var_type)
                var_res = None
                for f in v:
                    assert hasattr(var_type, f)
                    var_val  = getattr(var_type, f)
                    if var_res is None:
                        var_res = var_val
                    else:
                        var_res |= var_val
                    print(f"    f {f:16s} var_val {var_val:32s} {var_val.value:6d}")
                print("        ENUM FLAG ATTRIBUTE", k , v)
                print("        ENUM FLAG ATTRIBUTE", k , var_res)
                print("        ENUM FLAG ATTRIBUTE", k , var_res.value)
                try:
                    setattr(config, k, var_res.value)
                    has_channel_update = True
                except AttributeError:
                    print(f"  FAILED SETING {k}")
                    raise

            elif issubclass(var_type, Enum):
                assert hasattr(var_type, v)
                var_val  = getattr(var_type, v)
                print("SETTING ENUM ATTRIBUTE", k ,v, var_val.value, var_type)

            elif isinstance(var_type, Empty):
                print("SETTING EMPTY ATTRIBUTE", k ,v, var_type)
                try:
                    setattr(config, k, None)
                    has_channel_update = True
                except AttributeError:
                    print(f"  FAILED SETING {k}")
                    raise

            else:
                print("SETTING ATTRIBUTE", k ,v, var_type)
                try:
                    setattr(config, k, v)
                    has_channel_update = True
                except AttributeError:
                    print(f"  FAILED SETING {k}")
                    raise

        return has_channel_update


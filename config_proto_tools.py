import typing
import dataclasses
import json
import yaml

from enum import Enum, Flag as EnumFlag

class Empty:
    def to_json(self):
        return None

    @classmethod
    def to_yaml(cls, dumper, data):
        return None

    def __repr__(self):
        return '<Empty>'

yaml.add_representer(Empty, lambda dumper, data: None)
yaml.SafeDumper.add_representer(Empty, lambda dumper, data: yaml.representer.SafeRepresenter.represent_str(dumper, "EMPTY"))

empty = Empty()



class DataClassSerializer:
    def dict_factory(self, val: typing.List[typing.Tuple[str, typing.Any]], delete_empty=True):
        data = {k:v for k,v in val}
        if delete_empty:
            data = {k:v for k,v in data.items() if v is not None and not isinstance(v, Empty)}
        return data if data else None

    def as_dict(self):
        data = dataclasses.asdict(self, dict_factory=self.dict_factory)
        return data if data else None

    def as_template(self):
        data = dataclasses.asdict(self, dict_factory=lambda v: self.dict_factory(v, delete_empty=False))
        return data

    def to_json(self):
        return self.as_dict()

    @classmethod
    def get_empty(cls):
        kwargs = {}
        resolved_hints = typing.get_type_hints(cls)
        for k in dataclasses.fields(cls):
            name  = k.name
            vtype = resolved_hints[name]
            # print(name, vtype)
            if isinstance(vtype,type) and issubclass(vtype, DataClassSerializer):
                kwargs[name] = vtype.get_empty().as_template()
        return cls(**kwargs)

    @classmethod
    def from_dict(cls, kwargs):
        resolved_hints = typing.get_type_hints(cls)
        for k in dataclasses.fields(cls):
            name  = k.name
            vtype = resolved_hints[name]
            # print(name, vtype)
            if name in kwargs:
                if isinstance(vtype,type) and issubclass(vtype, DataClassSerializer):
                    val  = kwargs[k.name]
                    if val is None:
                        nval = val
                    else:
                        nval = vtype.from_dict(val)
                    kwargs[name] = nval
        return cls(**kwargs)

    def __str__(self):
        return json.dumps(self, indent=1)

    def __repr__(self):
        return str(self)



class AttributeChanger:
    def apply_changes(self, interface, config):
        resolved_hints = typing.get_type_hints(self)
        # print("SELF  ", self, self.__class__)
        # print("CONFIG", config, config.__class__, config.ListFields())
        opts = {}
        for o, v in config.ListFields():
            # print(o.name, v)
            opts[o.name] = v
        print(opts)

        d = self.as_dict()
        if d is None:
            return None

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
                    print(f"    f {f} var_val {var_val}")
                print(f"  var_inst {var_res} {var_res.value}")
                try:
                    setattr(config, k, var_res.value)
                except AttributeError:
                    print(f"  FAILED SETING {k}")
                    pass

            elif issubclass(var_type, Enum):
                print("SETTING ENUM ATTRIBUTE", k ,v, var_type)
                pass

            elif isinstance(var_type, Empty):
                print("SETTING EMPTY ATTRIBUTE", k ,v, var_type)
                #TODO: delete attribute value
            else:
                print("SETTING ATTRIBUTE", k ,v, var_type)
                try:
                    setattr(config, k, v)
                except AttributeError:
                    print(f"  FAILED SETING {k}")
                    pass


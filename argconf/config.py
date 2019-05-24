from collections import ChainMap, defaultdict
import argparse
import json
import os
import sys


class ConfigOption(object):

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.kwargs = kwargs
        if "type" in kwargs:
            kwargs["type"] = _options_map[kwargs["type"]]
        del kwargs["name"]

    def add_arg(self, parser):
        parser.add_argument(f"--{self.name}", **self.kwargs)


def options_from_json(filename):
    with open(filename) as f:
        json_list = json.load(f)
    option_dict = {item["name"]: ConfigOption(**item) for item in json_list}
    return option_dict


def config_from_json(filename):
    with open(filename) as f:
        cmap = json.load(f)
    if "_inherits_" in cmap:
        paths = cmap["_inherits_"]
        if isinstance(paths, str):
            paths = [paths]
        for inherits_path in paths:
            if not os.path.isabs(inherits_path):
                inherits_path = os.path.join(os.path.dirname(filename), inherits_path)
            parent_cmap = config_from_json(inherits_path)
            cmap = parent_cmap.new_child(cmap)
    else:
        cmap = ChainMap(cmap)
    return cmap


def parse_args(option_dict, config=None, **parser_kwargs):
    parser = argparse.ArgumentParser(**parser_kwargs)
    for option in option_dict.values():
        option.add_arg(parser)
    args, _ = parser.parse_known_args()
    if config is None:
        config = ChainMap()
    parse_vars = vars(args)
    parse_var_names = set(parse_vars.keys())
    argv_names = list(filter(lambda x: x.startswith("--"), sys.argv))

    dest_map = {}
    for action in parser._actions:
        for option_str in action.option_strings:
            dest_map[option_str] = action.dest
    argv_names = set([dest_map.get(argv, "") for argv in argv_names])

    for del_name in parse_var_names - argv_names:
        del parse_vars[del_name]

    cmap = config.new_child(parse_vars)
    flat_conf = {}
    for conf in reversed(cmap.maps):
        flat_conf.update(conf)
    try:
        del flat_conf["_inherits_"]
    except:
        pass
    return flat_conf


_options_map = dict(int=int, str=str, float=float, bool=bool)


def main_test():
    option_dict = options_from_json("examples/options.json")
    print(option_dict)
    local_config = config_from_json("examples/local.json")
    print(local_config)
    print(parse_args(option_dict, local_config))


if __name__ == "__main__":
    main_test()
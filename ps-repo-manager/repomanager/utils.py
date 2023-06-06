from typing import Any, Dict, TextIO

import yaml


class YamlIndentDumper(yaml.Dumper):
    """Helper class to allow for Ansible style indentation"""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        super().increase_indent(flow, False)


def yaml_dump(data: Dict[Any, Any], file: TextIO, sort_keys: bool = False) -> Any:
    """Call to yaml.dump() using customised style

    Args:
        data: A dict containing the data to be written as YAML.
        file: The file object to which to write the YAML data.
        sort_keys: Whether to sort keys alphabetically when writing to file (default: False).

    Returns:
        The result of yaml.dump().
    """
    return yaml.dump(
        data=data,
        stream=file,
        default_flow_style=False,
        sort_keys=sort_keys,
        Dumper=YamlIndentDumper,
    )


def deep_merge_dict(base, merge):

    return_dict = {**base}

    for key, value in merge.items():

        if isinstance(value, dict):

            if key in base:
                assert isinstance(base[key], dict)  # noqa S101 defensive mech until more mature

            return_dict[key] = deep_merge_dict(base.get(key, {}), value)
        # FIXME need a method to also support override
        elif isinstance(value, list) and (key in base):

            if key in base:
                assert isinstance(base[key], list)  # noqa S101 defensive mech until more mature

            return_dict[key] = base[key] + value
        elif value is None or value in ("__ps-sre__None", "__repo-manager__None"):
            try:
                del return_dict[key]
            except KeyError:
                pass
        else:
            return_dict[key] = value

    return return_dict

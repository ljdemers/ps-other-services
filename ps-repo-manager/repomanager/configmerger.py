import configparser
import os

import toml
import yaml

from repomanager.utils import deep_merge_dict, yaml_dump


class FileHandler:
    def __init__(self, path):
        self._path = path

    def _load_file(self):

        with open(self._path, "r") as file_object:
            return self._process_file(file_object)

    def _process_file(self, file_object):
        raise NotImplementedError

    def merge(self, merge_handler):
        raise NotImplementedError


class DictFileHandler(FileHandler):
    def get_dict(self):
        return self._load_file()

    def _save_dict(self):
        raise NotImplementedError

    def _merge_dict(self, dict_to_merge):

        current_dict = self.get_dict()

        merged_dict = deep_merge_dict(current_dict, dict_to_merge)

        self._save_dict(merged_dict)

    def merge(self, merge_handler):

        self._merge_dict(merge_handler.get_dict())


class TomlFileHandler(DictFileHandler):
    def _process_file(self, file_object):
        return toml.load(file_object)

    def _save_dict(self, dict_to_save):
        with open(self._path, "w") as file_object:
            toml.dump(dict_to_save, file_object)


class YamlFileHandler(DictFileHandler):
    def _process_file(self, file_object):
        return yaml.safe_load(file_object)

    def _save_dict(self, dict_to_save):
        with open(self._path, "w") as file_object:
            yaml_dump(dict_to_save, file_object)


class CfgFileHandler(DictFileHandler):
    def _process_file(self, file_object):

        config = configparser.ConfigParser()
        config.read(file_object)

        return {section: dict(config.items(section)) for section in config.sections()}

    def _save_dict(self, dict_to_save):
        with open(self._path, "w") as file_object:

            config = configparser.ConfigParser(dict_to_save)
            config.write(file_object)


HANDLERS = {
    "toml": TomlFileHandler,
    "toml.merge": TomlFileHandler,
    "yaml": YamlFileHandler,
    "yaml.merge": YamlFileHandler,
    "yml": YamlFileHandler,
    "yml.merge": YamlFileHandler,
    "cfg": CfgFileHandler,
    "cfg.merge": CfgFileHandler,
}


def verify_matching_extensions(configs):

    extension = _get_extension(configs[0])

    for config in configs[1:]:

        # FIXME replace with error handling
        assert _get_extension(config) == extension  # noqa S101 replace with error handling


def get_handler(path):

    try:
        return HANDLERS[_get_extension(path)](path)
    except KeyError:
        # FIXME use common exception class
        raise Exception(f'No merge handler for file extension "{_get_extension(path)}"')


def _get_extension(path):
    return os.path.splitext(path)[1][1:]

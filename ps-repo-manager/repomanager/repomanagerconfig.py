import logging
import os

import cerberus
import yaml

from repomanager.constants import REPO_MANAGER_DIRECTORY_PATH
from repomanager.exceptions import ConfigurationValidationError
from repomanager.utils import yaml_dump

logger = logging.getLogger()

CURRENT_CONFIG_VERSION = 1
CONFIG_VERSIONS_SUPPORTED = (CURRENT_CONFIG_VERSION,)

CONFIG_PATH = REPO_MANAGER_DIRECTORY_PATH + "config.yml"
CONFIG_SCHEMA = {
    "version": {"type": "integer", "allowed": CONFIG_VERSIONS_SUPPORTED},
    "repo_type": {"type": "string", "allowed": ["service", "library"]},
    "profiles": {
        "type": "list",
        "schema": {"type": "string"},
        # "allowed": ["python", "docker", "python-library-poetry", "docker-publish"], # FIXME check against config repo
    },
    "tests": {
        "type": "dict",
        "schema": {
            "pr": {
                "type": "list",
            }
        },
    },
    "owners": {
        "type": "list",
        "schema": {"type": "string"},
    },  # primary owner usernames e.g. edward.kirk
    "connected_users": {
        "type": "list",
        "schema": {"type": "string"},
    },  # secondary developers, team leads, pr reviews, etc.
    "template_values": {"type": "dict"},
    "exclude_files": {
        "type": "list",
        "schema": {"type": "string"},
    },
}

DEFAULT_CONFIG = {
    "version": CURRENT_CONFIG_VERSION,
    "profiles": [],
    # FIXME harcoded workaround for missing delete functionality - prioritise removal
    "exclude_files": [".github/workflows/pr.yml"],
}


def get_config(create_when_missing=False):

    config = _read_config(create_when_missing)

    _validate_config(config)

    return config


def save_config(config):

    _validate_config(config)

    _write_config(config)


def config_exists():

    return os.path.exists(CONFIG_PATH)


def _validate_config(config):

    validator = cerberus.Validator(CONFIG_SCHEMA)

    validator.validate(config)

    if validator.errors:
        logger.error("Config file issue: {validator.errors}")
        raise ConfigurationValidationError(validator.errors)

    # FIXME add general error handling for CLI
    assert not validator.errors  # noqa B101 adds some defense to immature code in the short term


def _create_config_directory():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)


def _read_config(create_when_missing):

    if create_when_missing:
        _create_config_directory()

    try:
        with open(CONFIG_PATH, "r") as config:
            try:
                return yaml.safe_load(config)
            except yaml.YAMLError:
                logger.error("Problem reading yaml file")
                raise
    except FileNotFoundError:

        _write_config(DEFAULT_CONFIG)
        return {**DEFAULT_CONFIG}


def _write_config(config):

    _create_config_directory()

    with open(CONFIG_PATH, "w") as config_file:
        yaml_dump(config, config_file)

import logging
from pathlib import Path

import cerberus
import yaml

from repomanager.constants import STATE_PATH
from repomanager.utils import yaml_dump

logger = logging.getLogger()

STATE_SCHEMA = {
    "config": {
        "type": "dict",
        "schema": {
            "installed_version": {"type": "string"},
            "installed_config": {"type": "dict"},
        },
    }
}

DEFAULT_STATE = {"config": {}}


class StateManager:
    def __init__(self, state_file_path):

        self._state_file_path = Path(state_file_path)

        # Ensure config dir exists
        try:
            self._state_file_path.parent.mkdir(parents=True)
        except FileExistsError:
            pass

        self.state = self._get_current_state()

    def _get_current_state(self):

        try:
            with open(self._state_file_path, "r") as state_file:
                current_state = yaml.safe_load(state_file)

                self.first_run = False
                return State(current_state, self._inner_state_updated)
        except FileNotFoundError:
            self.first_run = True
            return State(DEFAULT_STATE, self._inner_state_updated)

    def _inner_state_updated(self):

        # FIXME check against schema

        self._save_state()

    def _validate_state(self):

        validator = cerberus.Validator(STATE_SCHEMA)

        validator.validate(self.state)

        if validator.errors:
            logger.error("State issue: {validator.errors}")

        # FIXME replace with error handling
        assert not validator.errors  # noqa S101 replace with error handling

    def _save_state(self):

        state_dict = self.state.to_pure_dict()

        with open(self._state_file_path, "w") as state_file:
            yaml_dump(state_dict, state_file)


class State(dict):
    def __init__(self, dict_basis_arg=None, value_changed_callback=None):

        dict_basis_arg = dict_basis_arg or {}

        self._value_changed_callback = value_changed_callback

        dict_basis = {}
        for key, value in dict_basis_arg.items():
            dict_basis[key] = self._value_to_state(value)

        # kwargs not supported
        super().__init__(dict_basis)

    def _value_to_state(self, value):
        if isinstance(value, dict):
            return State(value, self._value_changed_callback)
        else:
            return value

    def __setitem__(self, key, value):
        # If new item is dict, use State instead
        super().__setitem__(key, self._value_to_state(value))

        if self._value_changed_callback:
            self._value_changed_callback()

    def to_pure_dict(self):

        # Recursive but should be ok for scope
        return_dict = {}

        for key, value in self.items():
            if isinstance(value, State):
                return_dict[key] = value.to_pure_dict()
            else:
                return_dict[key] = value
        return return_dict


state_manager = StateManager(STATE_PATH + "state.yml")

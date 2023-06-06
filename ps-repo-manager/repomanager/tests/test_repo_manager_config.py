import pytest

from repomanager.repomanagerconfig import ConfigurationValidationError, get_config, save_config


def test_save_config(temp_dir_chdir):

    valid_config = {"profiles": ["test"], "version": 1}

    # Test with no existing config file
    save_config(valid_config)

    saved_config = get_config()
    assert saved_config == valid_config

    # Test overriding current config
    modified_valid_config = {**valid_config, "profiles": ["test2", "test3"]}

    save_config(modified_valid_config)

    saved_config = get_config()
    assert saved_config == modified_valid_config

    # Test invalid config
    with pytest.raises(ConfigurationValidationError):
        save_config({**valid_config, "something": "invalid"})

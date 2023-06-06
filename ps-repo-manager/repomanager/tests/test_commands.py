import itertools
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Set, Union
from unittest import mock

import pytest
import yaml
from git import Repo
from path import Path

import repomanager.commands as commands_module
import repomanager.configrepo as configrepo_module
from repomanager.commands import (
    BOOTSTRAP_PREFIX,
    GIT_REPO_NON_BARE_MSG,
    GIT_REPO_NOT_ROOT_MSG,
    MERGING_CONFIGS_PATH,
    PREVIOUS_CONFIGS_STATE_PATH,
    RE_RUN_DIRTY_MSG,
    RE_RUN_INIT_MSG,
    BuildCommand,
    ConfigCommand,
    GitRepositoryError,
    InitCommand,
    RerunError,
    UpdateCommand,
)
from repomanager.configrepo import FIELD_NAME_GROUPS
from repomanager.constants import (
    CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME,
    CONFIG_REPO_PROFILE_CONFIG_FILE_NAME,
    STATE_PATH,
)
from repomanager.repomanagerconfig import CONFIG_PATH, DEFAULT_CONFIG
from repomanager.statemanager import StateManager

FAKE_CONFIG_REPO_VERSIONS = ["3.3.3", "2.2.2", "1.1.1"]

FAKE_PROFILE_NAMES = [
    "all",
    "profile_1",
    "profile_2",
    "python_profile",
]

FAKE_PYPROJECT = '\n[tool.poetry]\nname = "project-name"'

FAKE_LOCAL_FILES = {
    "irrelevant_local.txt": {
        "data": "irrelevant_data",
    },
    "irrelevant_local_dir": {
        "files": {
            "irrelevant_local_too.txt": {
                "data": "irrelevant",
            },
        },
    },
    "nested": {
        "files": {
            "merge.file.yml": {
                "data": {
                    "section": {"subsection_2": "additional_data"},
                },
            },
        },
    },
    "merge.file_2.yml": {
        "data": {
            "another_section": {"some_subsection": "even_more_data"},
        }
    },
    # Scenario where the project contains a pyproject.toml (e.g. repo-manager).
    "pyproject.toml": {
        "data": FAKE_PYPROJECT,
    },
}

FAKE_LOCAL_FILES_WITH_CONFIG = {
    **FAKE_LOCAL_FILES,
    ".repomanager": {
        "files": {
            "config.yml": {
                "data": DEFAULT_CONFIG,
            }
        },
    },
}

FAKE_STATE = {
    "config": {
        "installed_version": FAKE_CONFIG_REPO_VERSIONS[1],
        "failed_merges": [],
        "installed_config": DEFAULT_CONFIG,
    }
}

FAKE_LOCAL_FILES_WITH_CONFIG_AND_STATE = {
    **FAKE_LOCAL_FILES,
    ".repomanager": {
        "files": {
            "config.yml": {
                "data": DEFAULT_CONFIG,
            },
            "state": {
                "files": {
                    "state.yml": {
                        "data": FAKE_STATE,
                    },
                },
                "configs": {
                    "files": {
                        "pyproject.toml": {
                            "data": FAKE_PYPROJECT,
                        },
                    },
                },
            },
        },
    },
}

FAKE_REPO_CONFIG_WITH_PROFILES = {
    **DEFAULT_CONFIG,
    "profiles": [FAKE_PROFILE_NAMES[1], FAKE_PROFILE_NAMES[3]],
}

FAKE_LOCAL_FILES_WITH_PROFILES_CONFIG_AND_STATE = {
    **FAKE_LOCAL_FILES,
    ".repomanager": {
        "files": {
            "config.yml": {
                "data": FAKE_REPO_CONFIG_WITH_PROFILES,
            },
            "state": {
                "files": {
                    "state.yml": {
                        "data": FAKE_STATE,
                    },
                },
                "configs": {
                    "files": {
                        "pyproject.toml": {
                            "data": FAKE_PYPROJECT,
                        },
                    },
                },
            },
        },
    },
}

# Data used to tests commands with different ConfigRepo versions.
TEST_DATA_CONFIG_REPO_VERSIONS = (
    # Version string is None: the expected chosen version is the first returned by
    # ConfigRepo.list_versions().
    (
        None,
        FAKE_CONFIG_REPO_VERSIONS[0],
    ),
    # Version string set to some valid version, the expected chosen version is the same.
    (
        FAKE_CONFIG_REPO_VERSIONS[2],
        FAKE_CONFIG_REPO_VERSIONS[2],
    ),
)

# The following defines data used to test UpdateCommand.run() with different selected profiles.

TEST_REL_PATH_MERGED_FILE = "nested/file.yml"

# Expected values with only the 'all' profile selected.
EXPECTED_REL_PATHS_MERGED_ALL: Set[str] = {
    TEST_REL_PATH_MERGED_FILE,
    "file_2.yml",
    ".repomanager/state/configs/nested/file.yml",
    ".repomanager/state/configs/file_2.yml",
    "pyproject.toml",
}

EXPECTED_REL_PATHS_OTHER_ALL: Set[str] = {
    "irrelevant_local.txt",
    "irrelevant_local_dir/irrelevant_local_too.txt",
    ".repomanager/config.yml",
    ".repomanager/state/state.yml",
    "common_file",
    "merge.file_2.yml",
}

EXPECTED_CONTENT_MERGE_FILE_ALL: Dict[str, Any] = {
    "section": {
        "subsection_1": "some_data",
        "subsection_2": "additional_data",
    }
}

EXPECTED_PROFILES_ALL: List[str] = FAKE_PROFILE_NAMES[0:1]

# Expected values with the 'all' and 'profile_1' profiles selected.
EXPECTED_REL_PATHS_MERGED_PROFILE_1: Set[str] = {
    TEST_REL_PATH_MERGED_FILE,
    "file_2.yml",
    ".pre-commit-config.yml",
    ".repomanager/state/configs/.pre-commit-config.yml",
    ".repomanager/state/configs/nested/file.yml",
    "profile_1_file.txt",
}

EXPECTED_REL_PATHS_OTHER_PROFILE_1: Set[str] = {
    "irrelevant_local.txt",
    "irrelevant_local_dir/irrelevant_local_too.txt",
    ".repomanager/config.yml",
    ".repomanager/state/state.yml",
    "common_file",
    "nested/merge.file.yml",
    "merge.file_2.yml",
}

EXPECTED_CONTENT_MERGE_FILE_PROFILE_1: Dict[str, Any] = {
    "section": {
        "subsection_1": "some_data",
        "subsection_2": "additional_data",
        "subsection_3": "profile_2_data",
    }
}

# List of expected profiles when 'all' and 'profile_1' have been selected.
EXPECTED_PROFILES_PROFILE_1: List[str] = [
    FAKE_PROFILE_NAMES[0],
    FAKE_PROFILE_NAMES[1],
    FAKE_PROFILE_NAMES[3],
]

TEST_DATA_UPDATE_COMMAND_RUN = (
    (
        FAKE_LOCAL_FILES_WITH_CONFIG_AND_STATE,
        TEST_REL_PATH_MERGED_FILE,
        EXPECTED_PROFILES_ALL,
        EXPECTED_REL_PATHS_MERGED_ALL,
        EXPECTED_REL_PATHS_OTHER_ALL,
        EXPECTED_CONTENT_MERGE_FILE_ALL,
    ),
    (
        FAKE_LOCAL_FILES_WITH_PROFILES_CONFIG_AND_STATE,
        TEST_REL_PATH_MERGED_FILE,
        EXPECTED_PROFILES_PROFILE_1,
        EXPECTED_REL_PATHS_MERGED_PROFILE_1,
        EXPECTED_REL_PATHS_OTHER_PROFILE_1,
        EXPECTED_CONTENT_MERGE_FILE_PROFILE_1,
    ),
)


def _assert_files_and_directories_exist(
    spec: Mapping[str, Any], base_path: Union[Path, None] = None
) -> None:
    """Recursively check if the given files and directories exist at the expected path

    Args:
        spec: A mapping between the file/directory names and their content.
        base_path: The path in which to look for the files and directories specified in spec.
    """
    for local_path, content in spec.items():
        local_path = Path(local_path)
        rel_path = base_path / local_path if base_path else local_path

        if "files" in content:
            assert Path(rel_path).isdir()
            _assert_files_and_directories_exist(content["files"], base_path=rel_path)
        else:
            assert Path(rel_path).isfile()


@pytest.fixture
def mock_config_repo(monkeypatch, fake_repo):
    """Build mock ConfigRepo with predefined (fake) profiles"""

    fake_profiles_spec = {
        CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME: {
            "data": {
                FIELD_NAME_GROUPS: [
                    {
                        "name": "group-1",
                        "title": "Group 1",
                    },
                    {
                        "name": "group-2",
                        "title": "Group 2",
                    },
                ]
            },
        },
        "profiles": {
            "files": {
                FAKE_PROFILE_NAMES[0]: {
                    "files": {
                        "nested": {
                            "files": {
                                "file.yml": {
                                    "data": {
                                        "section": {"subsection_1": "some_data"},
                                    }
                                },
                            },
                        },
                        "bootstrap.common_file": {
                            "data": "bootstrap_data",
                        },
                        "file_2.yml": {
                            "data": {
                                "another_section": {"another_subsection": "more_data"},
                            },
                        },
                    },
                },
                FAKE_PROFILE_NAMES[1]: {
                    "files": {
                        CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                            "data": {
                                "depends_on": [FAKE_PROFILE_NAMES[2]],
                            },
                        },
                        "profile_1_file.txt": {
                            "data": "more_data",
                        },
                    },
                },
                FAKE_PROFILE_NAMES[2]: {
                    "files": {
                        "nested": {
                            "files": {
                                "file.yml": {
                                    "data": {
                                        "section": {
                                            "subsection_3": f"{FAKE_PROFILE_NAMES[2]}_data",
                                        },
                                    }
                                },
                            },
                        },
                    }
                },
                FAKE_PROFILE_NAMES[3]: {
                    "files": {
                        "merge..pre-commit-config.yml": {
                            "data": {
                                "repos": {
                                    "repo": "https://example.com/hooks",
                                    "rev": "v1.2.3",
                                    "hooks": {
                                        "id": "some-hook-id",
                                    },
                                },
                            },
                        },
                    },
                },
            }
        },
    }

    def mock_list_versions(*args, **kwargs):
        """Mock repo: Dummy versions"""
        return FAKE_CONFIG_REPO_VERSIONS

    def mock_checkout_version(*args, **kwargs):
        """Mock repo: No other versions supported"""

    monkeypatch.setattr(configrepo_module.ConfigRepo, "list_versions", mock_list_versions)
    monkeypatch.setattr(configrepo_module.ConfigRepo, "checkout_version", mock_checkout_version)

    fake_repo_path = fake_repo(fake_profiles_spec)
    return configrepo_module.ConfigRepo(repo_url=None, repo_path=fake_repo_path)


@pytest.fixture
def mock_get_config_repo(monkeypatch, mock_config_repo):
    """Monkey patching get_config_repo() to return mocked ConfigRepo with (fake) profiles"""

    def mock_get(*args, **kwargs):
        return mock_config_repo

    monkeypatch.setattr(commands_module, "get_config_repo", mock_get)

    return mock_config_repo


@pytest.mark.parametrize(
    "test_config_repo_version, expected_chosen_version", TEST_DATA_CONFIG_REPO_VERSIONS
)
def test_InitCommand_init_force_config_version(
    test_config_repo_version, expected_chosen_version, fake_repo, mock_get_config_repo, monkeypatch
):
    """Test basic instantiation of InitCommand with different config repo versions"""

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    # Fresh project, repo-manager config shouldn't exist yet.
    assert not (fake_repo_path / CONFIG_PATH).isfile()

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        cmd = InitCommand(force_config_repo_version=test_config_repo_version)

        assert commands_module.state_manager.first_run

        # Check if variables have been set correctly.
        assert cmd._force_config_repo_version == test_config_repo_version
        assert cmd.repo_manager_config == DEFAULT_CONFIG
        assert cmd.chosen_version == expected_chosen_version

        # Check if repo-manager directory and config file have been created.
        assert (fake_repo_path / CONFIG_PATH).isfile()

        # Check if all local files and directories are still there.
        _assert_files_and_directories_exist(FAKE_LOCAL_FILES, base_path=fake_repo_path)


@mock.patch.object(InitCommand, "_setup_config_repo")
@mock.patch.object(InitCommand, "_get_repo_manager_config")
def test_InitCommand_init_raises_not_in_repo(mock_setup, mock_get_config, tmp_path):
    """Test InitCommand in a directory that is not a git repo"""

    with Path(tmp_path), pytest.raises(GitRepositoryError) as exc_info:
        InitCommand()

    assert GIT_REPO_NOT_ROOT_MSG in str(exc_info.value)

    # Ensure that set-up methods have *not* been called if there was a problem with the repo.
    mock_get_config.assert_not_called()
    mock_setup.assert_not_called()


@mock.patch.object(InitCommand, "_setup_config_repo")
@mock.patch.object(InitCommand, "_get_repo_manager_config")
def test_InitCommand_init_raises_in_bare_repo(mock_setup, mock_get_config, tmp_path):
    """Test InitCommand in a bare git repo"""

    tmp_repo_path = Path(tmp_path)
    Repo.init(tmp_repo_path, bare=True)

    with tmp_repo_path, pytest.raises(GitRepositoryError) as exc_info:
        InitCommand()

    assert GIT_REPO_NON_BARE_MSG in str(exc_info.value)

    # Ensure that set-up methods have *not* been called if there was a problem with the repo.
    mock_get_config.assert_not_called()
    mock_setup.assert_not_called()


@mock.patch.object(InitCommand, "_setup_config_repo")
@mock.patch.object(InitCommand, "_get_repo_manager_config")
def test_InitCommand_init_raises_not_in_root_of_repo(mock_setup, mock_get_config, tmp_path):
    """Test InitCommand in a subdirectory of a non-bare git repo"""

    tmp_repo_path = Path(tmp_path)
    Repo.init(tmp_repo_path)

    sub_dir = tmp_repo_path / "sub-dir"
    sub_dir.makedirs_p()

    with sub_dir, pytest.raises(GitRepositoryError) as exc_info:
        InitCommand()

    assert GIT_REPO_NOT_ROOT_MSG in str(exc_info.value)

    # Ensure that set-up methods have *not* been called if there was a problem with the repo.
    mock_get_config.assert_not_called()
    mock_setup.assert_not_called()


@mock.patch.object(commands_module, "UpdateCommand")
def test_InitCommand_run(mock_update, fake_repo, mock_get_config_repo, monkeypatch):
    """Basic test of InitCommand.run()"""

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    # Fresh project, repo-manager config shouldn't exist yet.
    assert not (fake_repo_path / CONFIG_PATH).isfile()

    fake_selected_profiles = ["profile_1"]

    expected_config = {
        **DEFAULT_CONFIG,
        "profiles": fake_selected_profiles,
    }

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        # Mock profile selection to include additional profiles.
        with mock.patch.object(
            commands_module.ConfigCommand,
            "_prompt_user_select_profiles",
            return_value=fake_selected_profiles,
        ) as mock_select:
            cmd = InitCommand()
            cmd.run()

    mock_select.assert_called_once()
    mock_update.assert_called_once_with(cmd._force_config_repo_version)
    mock_update.return_value.run.assert_called_once_with()

    assert commands_module.state_manager.first_run

    # Check if repo-manager config file has been created.
    assert (fake_repo_path / CONFIG_PATH).isfile()

    # Check if repo-manager config file has been updated with the selected profiles.
    updated_config = yaml.safe_load((fake_repo_path / CONFIG_PATH).read_text())
    assert updated_config == expected_config


def test_InitCommand_fail_not_first_run(fake_repo):
    """Test InitCommand() when it's not the first run in a repo"""

    # Set up repo that already contains a repo-manager config.
    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES_WITH_CONFIG))

    with fake_repo_path, pytest.raises(RerunError) as exc_info:
        InitCommand()

    assert RE_RUN_INIT_MSG in str(exc_info.value)

    # Check if repo-manager config file is still there.
    assert (fake_repo_path / CONFIG_PATH).isfile()

    # Check if all local files and directories are still there.
    _assert_files_and_directories_exist(FAKE_LOCAL_FILES_WITH_CONFIG, base_path=fake_repo_path)


def test_ConfigCommand_init(fake_repo, mock_get_config_repo, monkeypatch):
    """Test basic instantiation of ConfigCommand with existing repo-manager config and state"""

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES_WITH_PROFILES_CONFIG_AND_STATE))

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        ConfigCommand()

    # Check if all local files and directories are still there.
    _assert_files_and_directories_exist(
        FAKE_LOCAL_FILES_WITH_PROFILES_CONFIG_AND_STATE, base_path=fake_repo_path
    )


def test_ConfigCommand_run_success(fake_repo, mock_get_config_repo, monkeypatch):
    """Basic test of ConfigCommand.run()"""

    fake_selected_profiles = FAKE_PROFILE_NAMES[2:3]

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES_WITH_PROFILES_CONFIG_AND_STATE))

    # Check if repo-manager config contains the right profiles.
    config_data = yaml.safe_load((fake_repo_path / CONFIG_PATH).read_text())
    assert config_data["profiles"] == FAKE_REPO_CONFIG_WITH_PROFILES["profiles"]

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        # Mock profile selection to include additional profiles.
        with mock.patch.object(
            commands_module.ConfigCommand,
            "_prompt_user_select_profiles",
            return_value=fake_selected_profiles,
        ) as mock_select:
            cmd = ConfigCommand()
            cmd.run()

    mock_select.assert_called_once()

    # Check if repo-manager config has been updated with the selected profiles.
    config_data = yaml.safe_load((fake_repo_path / CONFIG_PATH).read_text())
    assert config_data["profiles"] == fake_selected_profiles


def test_BuildCommand_init(fake_repo, mock_get_config_repo, monkeypatch):
    """Test basic instantiation of BuildCommand with existing repo-manager config and state"""

    fake_state = {
        "config": {
            "installed_version": "2.2.2",
            "failed_merges": [],
            "installed_config": DEFAULT_CONFIG,
        }
    }

    fake_local_files_with_config_and_state = deepcopy(FAKE_LOCAL_FILES_WITH_CONFIG)
    fake_local_files_with_config_and_state[".repomanager"]["files"]["state"] = {
        "files": {
            "state.yml": {
                "data": fake_state,
            },
        },
    }

    expected_repo_manager_config = fake_local_files_with_config_and_state[".repomanager"]["files"][
        "config.yml"
    ]["data"]
    expected_chosen_version = fake_state["config"]["installed_version"]

    # BuildCommand should work with existing repo-manager config.
    fake_repo_path = Path(fake_repo(fake_local_files_with_config_and_state))

    with fake_repo_path:
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        cmd = BuildCommand()

    # Check if variables have been set correctly.
    assert cmd._force_config_repo_version == expected_chosen_version
    assert cmd.repo_manager_config == expected_repo_manager_config
    assert cmd.chosen_version == expected_chosen_version

    # Check if all local files and directories are still there.
    _assert_files_and_directories_exist(
        fake_local_files_with_config_and_state, base_path=fake_repo_path
    )


@pytest.mark.parametrize(
    "test_command, expected_err_msg",
    (
        (UpdateCommand, RE_RUN_DIRTY_MSG),
        (BuildCommand, RE_RUN_DIRTY_MSG),
        (ConfigCommand, RE_RUN_DIRTY_MSG),
    ),
)
def test_Command_init_fail_on_first_run(test_command, expected_err_msg, fake_repo, monkeypatch):
    """Test different `Command` sub-class instantiations with missing repo-manager config file"""

    # Set up repo that doesn't contain a repo-manager config.
    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    with fake_repo_path, pytest.raises(RerunError) as exc_info:
        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        test_command()

    assert expected_err_msg in str(exc_info.value)

    # Ensure repo-manager config file hasn't been generated.
    assert not (fake_repo_path / CONFIG_PATH).isfile()

    # Check if all local files and directories are still there.
    _assert_files_and_directories_exist(FAKE_LOCAL_FILES, base_path=fake_repo_path)


@pytest.mark.parametrize(
    "test_config_repo_version, expected_chosen_version", TEST_DATA_CONFIG_REPO_VERSIONS
)
def test_UpdateCommand_init_force_config_version(
    test_config_repo_version, expected_chosen_version, fake_repo, mock_get_config_repo, monkeypatch
):
    """Test basic instantiation of UpdateCommand with different config repo versions"""

    fake_state = {
        "config": {
            "installed_version": "2.2.2",
            "failed_merges": [],
            "installed_config": DEFAULT_CONFIG,
        }
    }

    fake_local_files_with_config_and_state = deepcopy(FAKE_LOCAL_FILES_WITH_CONFIG)
    fake_local_files_with_config_and_state[".repomanager"]["files"]["state"] = {
        "files": {
            "state.yml": {
                "data": fake_state,
            },
        },
    }

    # UpdateCommand should work with existing repo-manager config and state file.
    fake_repo_path = Path(fake_repo(fake_local_files_with_config_and_state))

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        cmd = UpdateCommand(force_config_repo_version=test_config_repo_version)

        assert not commands_module.state_manager.first_run

        # Check if variables have been set correctly.
        assert cmd._force_config_repo_version == test_config_repo_version
        assert cmd.repo_manager_config == DEFAULT_CONFIG
        assert cmd.chosen_version == expected_chosen_version

        # Check if repo-manager directory and config file have been created.
        assert (fake_repo_path / CONFIG_PATH).isfile()

        # Check if all local files and directories are still there.
        _assert_files_and_directories_exist(
            fake_local_files_with_config_and_state, base_path=fake_repo_path
        )


@pytest.mark.parametrize(
    "test_local_files,"
    "test_rel_path_merged_file,"
    "expected_profiles,"
    "expected_rel_paths_merged,"
    "expected_rel_paths_other,"
    "expected_content_merge_file,",
    TEST_DATA_UPDATE_COMMAND_RUN,
    ids=itertools.count(),
)
def test_UpdateCommand_run_different_profiles(
    test_local_files,
    test_rel_path_merged_file,
    expected_profiles,
    expected_rel_paths_merged,
    expected_rel_paths_other,
    expected_content_merge_file,
    fake_repo,
    mock_get_config_repo,
    monkeypatch,
):
    """Test UpdateCommand.run() with different selected profiles"""

    # UpdateCommand should work with existing repo-manager config file.
    fake_repo_path = Path(fake_repo(test_local_files))

    # Update all paths to point to the fake repo.
    expected_merged_paths: Set[Path] = {
        fake_repo_path / local_path for local_path in expected_rel_paths_merged
    }

    expected_other_paths: Set[Path] = {
        fake_repo_path / local_path for local_path in expected_rel_paths_other
    }

    expected_paths: Set[Path] = expected_merged_paths | expected_other_paths

    test_path_merged_file: Path = fake_repo_path / test_rel_path_merged_file

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        cmd = UpdateCommand()
        cmd.run()

        assert not commands_module.state_manager.first_run

        assert cmd.profiles == expected_profiles
        assert cmd.chosen_version == FAKE_CONFIG_REPO_VERSIONS[0]

        file_paths = set(fake_repo_path.walkfiles())

        for file_path in sorted(file_paths):
            assert not file_path.startswith(
                BOOTSTRAP_PREFIX
            ), f"Unexpected bootstrap file found: {file_path}"

        # Check if all expected files are there.
        missing_file_paths = expected_paths - file_paths
        assert not missing_file_paths, f"Unexpected missing paths: {missing_file_paths}"

        # Check if all local files and directories are still there.
        _assert_files_and_directories_exist(test_local_files, base_path=fake_repo_path)

        merged_data = yaml.safe_load(test_path_merged_file.read_text())
        assert merged_data == expected_content_merge_file

        # Check if intermediate directories have been removed.
        assert not Path(PREVIOUS_CONFIGS_STATE_PATH).isdir()
        assert not Path(MERGING_CONFIGS_PATH).isdir()

        # Check if the correct state has been stored.
        state_config = commands_module.state_manager.state["config"]
        assert state_config["installed_version"] == cmd.chosen_version
        assert state_config["installed_config"] == cmd.repo_manager_config
        assert state_config["failed_merges"] == []


def test_init_and_update_failed_merges_changed_file(
    capsys, fake_repo, mock_get_config_repo, monkeypatch
):
    """Run InitCommand and UpdateCommand with failed merge because of changes to local file"""

    expected_merge_file_content = {
        "section": {
            "subsection_1": "some_data",
            "subsection_2": "additional_data",
        },
        "section_2": "some_data",
    }

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    merged_file_rel_path: Path = Path("nested/file.yml")
    merged_file_path: Path = fake_repo_path / merged_file_rel_path

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        init_cmd = InitCommand()
        init_cmd.run()

        # Manually change a file which is tracked by repo-manager.
        merged_file_path.write_text("section_2: some_data", append=True)

        update_cmd = UpdateCommand()
        update_cmd.run()

        stdout, stderr = capsys.readouterr()

        assert "Failed to generate the following files" in stdout
        assert merged_file_rel_path in stdout

        # Check if the all the data (including manually added) is still there.
        merged_data = yaml.safe_load(merged_file_path.read_text())
        assert merged_data == expected_merge_file_content

        # Check if intermediate directories have been removed.
        assert not Path(PREVIOUS_CONFIGS_STATE_PATH).isdir()
        assert not Path(MERGING_CONFIGS_PATH).isdir()

        # Check if the correct state has been stored.
        state_config = commands_module.state_manager.state["config"]
        assert state_config["installed_version"] == init_cmd.chosen_version
        assert state_config["installed_config"] == init_cmd.repo_manager_config
        assert state_config["failed_merges"] == [merged_file_rel_path]


def test_init_and_update_merge_success_missing_file(
    capsys, fake_repo, mock_get_config_repo, monkeypatch
):
    """Run InitCommand and UpdateCommand with successful merge despite a missing file in state"""

    expected_merge_file_content = {
        "section": {
            "subsection_1": "some_data",
            "subsection_2": "additional_data",
        },
    }

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    merged_file_rel_path: Path = Path("nested/file.yml")
    merged_file_path: Path = fake_repo_path / merged_file_rel_path
    merged_file_state_path: Path = (
        fake_repo_path / ".repomanager" / "state" / "configs" / merged_file_rel_path
    )

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        init_cmd = InitCommand()
        init_cmd.run()

        # Remove file to be merged from state.
        merged_file_state_path.remove_p()

        update_cmd = UpdateCommand()
        update_cmd.run()

        stdout, stderr = capsys.readouterr()

        assert "Failed to generate the following files" not in stdout
        assert merged_file_rel_path not in stdout

        # Check if all the data (including manually added) is still there.
        merged_data = yaml.safe_load(merged_file_path.read_text())
        assert merged_data == expected_merge_file_content

        # Check if intermediate directories have been removed.
        assert not Path(PREVIOUS_CONFIGS_STATE_PATH).isdir()
        assert not Path(MERGING_CONFIGS_PATH).isdir()

        # Check if the correct state has been stored.
        state_config = commands_module.state_manager.state["config"]
        assert state_config["installed_version"] == init_cmd.chosen_version
        assert state_config["installed_config"] == init_cmd.repo_manager_config
        assert state_config["failed_merges"] == []


def test_init_and_update_excluded_file(capsys, fake_repo, mock_get_config_repo, monkeypatch):
    """Initialise and update project multiple times while excluding and changing a file

    Testing a scenario in which a file gets excluded from the project (using 'exclude_files') after
    the project has been initialised.

    The file then gets modified and included again.
    """

    expected_content_excluded_file = {
        "section": {
            "subsection_1": "some_data",
            "subsection_2": "additional_data",
        },
        "section_2": "some_data",
    }

    fake_repo_path = Path(fake_repo(FAKE_LOCAL_FILES))

    excluded_file_rel_path: Path = Path("nested/file.yml")
    excluded_file_path: Path = fake_repo_path / excluded_file_rel_path
    excluded_file_state_path: Path = (
        fake_repo_path / ".repomanager" / "state" / "configs" / excluded_file_rel_path
    )

    with fake_repo_path:

        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        # Initialise project.
        init_cmd = InitCommand()
        init_cmd.run()

        update_cmd = UpdateCommand()
        update_cmd.run()

        # File is *not* excluded yet.
        assert excluded_file_state_path.isfile()

        # Add `exclude_file` section to repo manager config file.
        repo_config_path = fake_repo_path / ".repomanager/config.yml"
        repo_config = yaml.safe_load((repo_config_path).read_text())
        repo_config["exclude_files"] = [str(excluded_file_rel_path)]

        yaml.dump(repo_config, repo_config_path.open("w"), default_flow_style=False)

        excluded_file_data_original = excluded_file_path.read_text()
        # Manual change to the excluded file should be ignored in the next UpdateCommand.run().
        excluded_file_path.write_text("section_2: some_data", append=True)

        # Re-run update command.
        update_cmd = UpdateCommand()
        update_cmd.run()

        # File *is* excluded now, there should be no merge issues.
        assert not excluded_file_state_path.isfile()

        stdout, stderr = capsys.readouterr()

        assert "Failed to generate the following files" not in stdout
        assert excluded_file_rel_path not in stdout

        # Check if all the data (including manually added) is still there.
        content_excluded_file = yaml.safe_load(excluded_file_path.read_text())
        assert content_excluded_file == expected_content_excluded_file

        # Check if intermediate directories have been removed.
        assert not Path(PREVIOUS_CONFIGS_STATE_PATH).isdir()
        assert not Path(MERGING_CONFIGS_PATH).isdir()

        # Check if the correct state has been stored.
        state_config = commands_module.state_manager.state["config"]
        assert state_config["installed_version"] == update_cmd.chosen_version
        assert state_config["installed_config"] == update_cmd.repo_manager_config
        assert state_config["failed_merges"] == []

        # Remove excluded file from repo manager config.
        del repo_config["exclude_files"]
        yaml.dump(repo_config, repo_config_path.open("w"), default_flow_style=False)

        # Re-run update command.
        update_cmd = UpdateCommand()
        update_cmd.run()

        # Manual change to the excluded file should be picked up again now.
        stdout, stderr = capsys.readouterr()

        assert "Failed to generate the following files" in stdout
        assert excluded_file_rel_path in stdout

        # Check if all the data (including manually added) is still there.
        content_excluded_file = yaml.safe_load(excluded_file_path.read_text())
        assert content_excluded_file == expected_content_excluded_file

        # Check if the correct state has been stored.
        state_config = commands_module.state_manager.state["config"]
        assert state_config["installed_version"] == update_cmd.chosen_version
        assert state_config["installed_config"] == update_cmd.repo_manager_config
        assert state_config["failed_merges"] == [excluded_file_rel_path]

        # Restore original content.
        excluded_file_path.write_text(excluded_file_data_original, append=False)

        # Re-run update command.
        update_cmd = UpdateCommand()
        update_cmd.run()

        # File is no longer excluded.
        assert excluded_file_state_path.isfile()

        stdout, stderr = capsys.readouterr()

        assert "Failed to generate the following files" not in stdout
        assert excluded_file_rel_path not in stdout


def test_build_success_on_changed_merge_file(capsys, fake_repo, mock_get_config_repo, monkeypatch):
    """Successfully run BuildCommand (in an initialised repo) after a merge file has been changed"""

    fake_state = {
        "config": {
            "installed_version": "2.2.2",
            "failed_merges": [],
            "installed_config": DEFAULT_CONFIG,
        }
    }

    fake_local_files_with_config_and_state = deepcopy(FAKE_LOCAL_FILES_WITH_CONFIG)
    fake_local_files_with_config_and_state[".repomanager"]["files"]["state"] = {
        "files": {
            "state.yml": {
                "data": fake_state,
            },
        },
    }

    fake_repo_path = Path(fake_repo(fake_local_files_with_config_and_state))

    merge_file_path: Path = fake_repo_path / "merge.file_2.yml"
    merged_file_path: Path = fake_repo_path / "file_2.yml"

    expected_merged_file_content = {
        "another_section": {
            "another_subsection": "more_data",
            "some_subsection": "even_more_data",
        },
        "additional_section": "some_data",
    }

    # Update the merge file.
    merge_file_path.write_text("additional_section: some_data", append=True)

    with fake_repo_path:
        # Manually reset state to ensure it picks up files in the current directory.
        monkeypatch.setattr(
            commands_module,
            "state_manager",
            StateManager(fake_repo_path / STATE_PATH / "state.yml"),
        )

        build_cmd = BuildCommand()
        build_cmd.run()

    stdout, stderr = capsys.readouterr()

    assert not stdout
    assert not stderr

    # Check if the all the data (including manually added) is in the final merged file.
    merged_data = yaml.safe_load(merged_file_path.read_text())
    assert merged_data == expected_merged_file_content

    # Check if intermediate directories have been removed.
    assert not Path(PREVIOUS_CONFIGS_STATE_PATH).isdir()
    assert not Path(MERGING_CONFIGS_PATH).isdir()

    # Check if the correct state has been stored.
    state_config = commands_module.state_manager.state["config"]
    assert state_config["installed_version"] == fake_state["config"]["installed_version"]
    assert state_config["installed_config"] == fake_state["config"]["installed_config"]
    assert state_config["failed_merges"] == []

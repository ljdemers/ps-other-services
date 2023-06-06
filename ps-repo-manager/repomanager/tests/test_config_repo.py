from collections import OrderedDict
from typing import List, Sequence

import pytest
from git import Repo
from path import Path

from repomanager.configrepo import FIELD_NAME_GROUPS, ConfigRepo
from repomanager.constants import (
    CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME,
    CONFIG_REPO_PROFILE_CONFIG_FILE_NAME,
)
from repomanager.exceptions import ConfigRepoError, ConfigurationValidationError


@pytest.fixture
def fake_config_repo_with_tags(fake_repo) -> Path:

    fake_config_files = {
        "profiles": {
            "files": {
                "profile_1": {
                    "files": {
                        "somefile.txt": {
                            "data": "somedata",
                        },
                    },
                },
                "profile_2": {
                    "files": {
                        CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                            "data": {
                                "depends_on": [
                                    "profile_3",
                                ],
                            },
                        },
                        "selected.txt": {
                            "data": "somedata",
                        },
                    },
                },
                "profile_3": {
                    "files": {
                        "somefile.txt": {
                            "data": "somedata",
                        },
                    },
                },
            }
        }
    }

    fake_new_files: List[Path] = [
        Path("profiles") / "profile_1" / "new_file_1.txt",
        Path("profiles") / "profile_2" / "new_file_2.txt",
    ]

    fake_tags = ["3.3.3", "2.2.2", "1.1.1"]

    # Set up test repo.
    repo_path = Path(fake_repo(fake_config_files))
    repo = Repo.init(repo_path)
    repo.index.add("profiles")
    repo.index.commit("Add profiles")

    # Branch doesn't exist before the first commit.
    repo.create_tag(fake_tags[2])

    # Invalid tag shouldn't show up in the list of version.
    repo.create_tag("invalid_tag")

    new_file_1 = repo_path / fake_new_files[0]
    new_file_1.write_text("some_data")

    # Create commit and tag for each added file.
    repo.index.add(new_file_1)
    repo.index.commit("Add new_file_1.txt")
    repo.create_tag(fake_tags[1])

    new_file_2 = repo_path / fake_new_files[1]
    new_file_2.write_text("more_data")

    repo.index.add(new_file_2)
    repo.index.commit("Add new_file_2.txt")
    repo.create_tag(fake_tags[0])

    return {
        "fake_repo_path": repo_path,
        "fake_tags": fake_tags,
        "fake_new_files": fake_new_files,
    }


def test_ConfigRepo_init_bad_config(fake_repo):
    """Test if exception is raised when the config file is missing a required field"""

    fake_repo_spec = {
        CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME: {
            "data": {
                FIELD_NAME_GROUPS: [
                    {
                        # Group is missing the required field `name`.
                        "title": "Group 1",
                        "description": "Group 1 description",
                    },
                ]
            },
        },
    }

    with pytest.raises(ConfigurationValidationError) as exc_info:
        ConfigRepo(None, fake_repo(fake_repo_spec))

    assert "name" in exc_info.value.args[0]
    assert "required field" in exc_info.value.args[0]


def test_ConfigRepo_init_config_invalid_yaml(fake_repo):
    """Test if an exception is raise if the config file contains invalid YAML"""

    fake_repo_spec = {
        CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME: {
            "data": {
                FIELD_NAME_GROUPS: [
                    {
                        "name": "group-1",
                        "title": "Group 1",
                        "description": "Group 1 description",
                    },
                    {
                        "name": "group-2",
                        "title": "Group 2",
                        "description": "Group 2 description",
                    },
                ]
            },
        },
    }

    fake_repo_path = Path(fake_repo(fake_repo_spec))

    fake_config = fake_repo_path / CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME

    invalid_yaml = ": invalid\n"

    fake_config.write_text(invalid_yaml, append=True)

    with pytest.raises(ConfigRepoError) as exc_info:
        ConfigRepo(None, fake_repo_path)

    assert invalid_yaml in exc_info.value.args[0]


def test_get_all_profile_names(fake_repo):

    repo_path = fake_repo(
        {
            "profiles": {
                "files": {
                    "profile1": {"files": {"somefile.txt": {"data": "somedata"}}},
                    "profile2": {
                        "files": {
                            CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                                "data": {"depends_on": ["profile3"]},
                            },
                            "selected.txt": {"data": "somedata"},
                        }
                    },
                    "profile3": {"files": {"somefile.txt": {"data": "somedata"}}},
                }
            }
        }
    )

    config_repo = ConfigRepo(None, repo_path)

    profiles = config_repo.get_all_profile_names()

    assert set(profiles) == set(["profile1", "profile2", "profile3"])


def test_list_configs_depends_on_multiple(fake_repo):

    repo_path = fake_repo(
        {
            "profiles": {
                "files": {
                    "selectedprofile": {
                        "files": {
                            CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                                "data": {"depends_on": ["nestedprofile_1", "nestedprofile_2"]},
                            },
                            "selected.txt": {"data": "visible1"},
                        }
                    },
                    "ignoredprofile_1": {"files": {"notvisible.txt": {"data": "notvisible"}}},
                    "nestedprofile_1": {"files": {"nested.txt": {"data": "visible1"}}},
                    "ignoredprofile_2": {"files": {"notvisible.txt": {"data": "notvisible"}}},
                    "nestedprofile_2": {"files": {"nested.txt": {"data": "visible1"}}},
                }
            }
        }
    )

    config_repo = ConfigRepo(None, repo_path)

    configs = config_repo.list_config_files(["selectedprofile"])

    assert configs == OrderedDict(
        [
            ("nestedprofile_1", ["nested.txt"]),
            ("nestedprofile_2", ["nested.txt"]),
            ("selectedprofile", ["selected.txt"]),
        ]
    )


def test_list_configs_depends_on_nested(fake_repo):

    repo_path = fake_repo(
        {
            "profiles": {
                "files": {
                    "ignoredprofile": {"files": {"notvisible.txt": {"data": "notvisible"}}},
                    "selectedprofile": {
                        "files": {
                            CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                                "data": {"depends_on": ["nestedprofile"]},
                            },
                            "selected.txt": {"data": "visible1"},
                        }
                    },
                    "nestedprofile": {
                        "files": {
                            CONFIG_REPO_PROFILE_CONFIG_FILE_NAME: {
                                "data": {"depends_on": ["doublenestedprofile"]},
                            },
                            "nested.txt": {"data": "visible1"},
                        }
                    },
                    "doublenestedprofile": {"files": {"doublenested.txt": {"data": "visible1"}}},
                }
            }
        }
    )

    config_repo = ConfigRepo(None, repo_path)

    configs = config_repo.list_config_files(["selectedprofile"])

    assert configs == OrderedDict(
        [
            ("doublenestedprofile", ["doublenested.txt"]),
            ("nestedprofile", ["nested.txt"]),
            ("selectedprofile", ["selected.txt"]),
        ]
    )


def test_get_group_config(fake_repo):

    fake_repo_spec = {
        CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME: {
            "data": {
                FIELD_NAME_GROUPS: [
                    {
                        "name": "group-1",
                        "title": "Group 1",
                        "description": "Group 1 description",
                    },
                    {
                        "name": "group-2",
                        "title": "Group 2",
                        "description": "Group 2 description",
                    },
                ]
            },
        },
    }

    config_repo = ConfigRepo(None, fake_repo(fake_repo_spec))

    assert (
        config_repo.get_group_config()[0]["title"]
        == fake_repo_spec[CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME]["data"][FIELD_NAME_GROUPS][0][
            "title"
        ]
    )


def test_get_group_config_missing_config(fake_repo):
    """Test if an emtpy list is returned if config file is missing"""

    config_repo = ConfigRepo(None, fake_repo({}))

    config = config_repo.get_group_config()

    assert isinstance(config, Sequence)
    assert not config


def test_ConfigRepo_list_version(fake_config_repo_with_tags):
    """Test if the right version are being listed"""

    fake_repo_path = fake_config_repo_with_tags["fake_repo_path"]
    fake_tags = fake_config_repo_with_tags["fake_tags"]

    config_repo = ConfigRepo(repo_url=None, repo_path=fake_repo_path)

    versions = config_repo.list_versions()

    assert versions == fake_tags


def test_ConfigRepo_checkout_version_valid_tag(fake_config_repo_with_tags):
    """Test if the right files are being checkout out if a version is specified"""

    fake_repo_path = fake_config_repo_with_tags["fake_repo_path"]
    fake_tags = fake_config_repo_with_tags["fake_tags"]
    fake_file_1, fake_file_2 = fake_config_repo_with_tags["fake_new_files"]

    config_repo = ConfigRepo(repo_url=None, repo_path=fake_repo_path)

    config_repo.checkout_version(fake_tags[1])

    all_files = list(fake_repo_path.walkfiles())

    assert fake_repo_path / fake_file_1 in all_files
    assert fake_repo_path / fake_file_2 not in all_files


def test_ConfigRepo_checkout_version_no_version(fake_config_repo_with_tags):
    """Test if the right files are being checkout out if no version is specified"""

    fake_repo_path = fake_config_repo_with_tags["fake_repo_path"]
    fake_file_1, fake_file_2 = fake_config_repo_with_tags["fake_new_files"]

    config_repo = ConfigRepo(repo_url=None, repo_path=fake_repo_path)

    config_repo.checkout_version(version=None)

    all_files = list(fake_repo_path.walkfiles())

    assert fake_repo_path / fake_file_1 in all_files
    assert fake_repo_path / fake_file_2 in all_files


def test_ConfigRepo_checkout_version_bad_version(fake_config_repo_with_tags):
    """Test if the right exception is raised when an invalid version is specified for checkout"""

    fake_repo_path = fake_config_repo_with_tags["fake_repo_path"]

    config_repo = ConfigRepo(repo_url=None, repo_path=fake_repo_path)

    with pytest.raises(ConfigRepoError):
        config_repo.checkout_version(version="bad_version")

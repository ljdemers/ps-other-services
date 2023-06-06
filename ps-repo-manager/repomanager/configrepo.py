import os
import sys
from collections import OrderedDict
from typing import Any, Iterable, List, MutableMapping, Sequence

import cerberus
import git
import path
import semver
import yaml
from git import TagReference

from repomanager.constants import (
    CACHE_PATH,
    CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME,
    CONFIG_REPO_PROFILE_CONFIG_FILE_NAME,
)
from repomanager.exceptions import ConfigRepoError, ConfigurationValidationError

Group = MutableMapping[str, Any]
Profile = MutableMapping[str, Any]
Config = MutableMapping[str, Any]

FIELD_NAME_GROUPS = "groups"

CONFIG_REPO_CONFIG_SCHEMA = {
    FIELD_NAME_GROUPS: {
        "type": "list",
        "schema": {
            "require_all": True,
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                },
                "title": {
                    "type": "string",
                },
                "description": {
                    "type": "string",
                    "required": False,
                },
            },
        },
    }
}
config_repo_config_validator = cerberus.Validator(CONFIG_REPO_CONFIG_SCHEMA)


class ConfigRepo:
    def __init__(self, repo_url: str, repo_path: str, default_branch: str = "main") -> None:

        self.repo_url = repo_url
        self.repo_path = repo_path
        self.default_branch = default_branch

        self._clone_repo()
        self._update_repo()

        self._read_config_file()

    def _clone_repo(self) -> None:

        if os.path.isdir(self.repo_path):

            self._repo = git.Repo(self.repo_path)

            return

        self._repo = git.Repo.clone_from(self.repo_url, self.repo_path)

        return

    def _update_repo(self) -> None:

        if self.repo_url:
            self._repo.remotes.origin.fetch()

    def _read_config_file(self) -> None:

        config_path = path.Path(self.repo_path) / CONFIG_REPO_GLOBAL_CONFIG_FILE_NAME

        try:
            config = yaml.safe_load(config_path.read_text())
        except FileNotFoundError:
            # Don't fail if the config file doesn't exist.
            config = {}
        except Exception as exc:
            raise ConfigRepoError(f"Unable to read config repo configuration: {exc}")

        valid = config_repo_config_validator.validate(config)

        if not valid:
            raise ConfigurationValidationError(
                "Config repo configuration validation failed with: "
                f"{config_repo_config_validator.errors}"
            )

        self._config = config

    def list_versions(self) -> List[str]:

        tags = self._repo.tags

        ordered_versions = self._parse_tags(tags)

        return ordered_versions

    def _parse_tags(self, tags: Iterable[TagReference]) -> List[str]:

        versions = []

        for tag in tags:
            try:
                versions.append(semver.VersionInfo.parse(str(tag)))
            except ValueError:
                continue

        versions.sort(reverse=True)

        return [str(version) for version in versions]

    def _check_clean(self) -> None:

        # FIXME add general error handling to CLI
        assert (  # noqa B101 adds some defense to immature code
            not self._repo.is_dirty()
        ), "Repo cache is not clean"

    def _get_language_dir(self, language: str) -> path.Path:

        return path.Path(self.repo_path) / path.Path("profiles") / path.Path(language)

    def checkout_version(self, version: str) -> None:

        self._check_clean()

        try:
            self._repo.git.checkout(version)
        except Exception as exc:
            raise ConfigRepoError(
                f"There was a problem with the config repo when checking out version '{version}': "
                f"{str(exc)}"
            )

    def _get_profile_config(self, profile: str) -> Profile:

        profile_config = {"name": profile, "path": self._get_language_dir(profile)}

        # Load config
        try:
            with open(
                profile_config["path"] / path.Path(CONFIG_REPO_PROFILE_CONFIG_FILE_NAME), "r"
            ) as file_object:
                profile_config = {**profile_config, **yaml.safe_load(file_object)}
        except FileNotFoundError:
            pass

        return profile_config

    def get_all_profile_names(self) -> List[str]:

        # Only iterate once
        for _full_path, dirs, _files in os.walk(path.Path(self.repo_path) / path.Path("profiles")):

            return dirs

        return []

    def get_profile_configs(self, profiles: Sequence[str]) -> List[Profile]:

        profile_configs = []

        for profile in profiles:

            profile_configs.append(self._get_profile_config(profile))

        return profile_configs

    def list_config_files(self, profiles: Sequence[str]) -> "OrderedDict[str, List[str]]":

        remaining_profiles = self.get_profile_configs(profiles)

        config_files: "OrderedDict[str, List[str]]" = OrderedDict()

        while remaining_profiles:

            profile = remaining_profiles.pop(0)

            if profile.get("depends_on"):

                depends_on: List[str] = profile["depends_on"]

                del profile["depends_on"]

                # Re-add this profile and then new profiles
                remaining_profiles[0:0] = self.get_profile_configs(depends_on) + [profile]
                continue

            config_files[profile["name"]] = []

            assert os.path.isdir(profile["path"])  # noqa B101 adds some defense to immature code

            config_files[profile["name"]] = []
            for directory, _, file_relative_paths in os.walk(profile["path"]):

                for file_relative in file_relative_paths:

                    if CONFIG_REPO_PROFILE_CONFIG_FILE_NAME == file_relative:
                        continue

                    long_relative_path = directory + "/" + file_relative

                    config_files[profile["name"]].append(
                        long_relative_path.replace(str(profile["path"]) + "/", "")
                    )

        return config_files

    def get_config_path(self, language: str, config: str) -> path.Path:

        language_dir = self._get_language_dir(language)

        return language_dir / config

    def get_group_config(self) -> List[Group]:

        return self._config.get(FIELD_NAME_GROUPS, [])


############
# def highest_version(version_a, version_b):
#
#    if version_a is None:
#        return version_b
#
#    if version_b.prerelease is not None and not re.match(r"dev\d+", version_b.prerelease):
#        return version_a
#
#    # semver incorrectly evals devX
#    comparison_a = semver.VersionInfo.parse(str(version_a).replace("dev", ""))
#    comparison_b = semver.VersionInfo.parse(str(version_b).replace("dev", ""))
#
#    if comparison_b > comparison_a:
#        return version_b
#    else:
#        return version_a
#
#
## print(highest_version(semver.VersionInfo.parse("3.1.10-dev9"), semver.VersionInfo.parse("3.1.10-dev10")))
#
# for line in sys.stdin:
#
#    try:
#        current_highest_version = highest_version(
#            current_highest_version, semver.VersionInfo.parse(line)
#        )
#    except:
#        continue
#
# if current_highest_version:
#    print(current_highest_version)
# else:
#    print("NO CURRENT VERSION FOUND - you must manually push the first tag in a new application")
#
################################
# clone repo

# switch versions

# return contents
module = sys.modules[__name__]
_default_config_repo = None


def get_config_repo():

    if not _default_config_repo:
        module._default_config_repo = ConfigRepo(
            "git@github.com:Pole-Star-Space-Applications-USA/repo-manager-configs.git",
            CACHE_PATH + "repo-configs",
        )

    return _default_config_repo

import filecmp
import os
import shutil
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from typing import DefaultDict, List, Union

from git import InvalidGitRepositoryError, Repo
from path import Path
from typer import colors, secho

from repomanager import configmerger
from repomanager.configrepo import get_config_repo
from repomanager.constants import CACHE_PATH, STATE_PATH
from repomanager.exceptions import GitRepositoryError, NotSupportedOnPythonVersion, RerunError
from repomanager.localfiles import gather_local_files
from repomanager.repomanagerconfig import config_exists, get_config, save_config
from repomanager.statemanager import state_manager
from repomanager.tui import ProfileSelection

CONFIGS_STATE_PATH = STATE_PATH + "configs/"
PREVIOUS_CONFIGS_STATE_PATH = STATE_PATH + "configs.previous/"
MERGING_CONFIGS_PATH = CACHE_PATH + "merging/"

BOOTSTRAP_PREFIX = "bootstrap."

GIT_REPO_NOT_ROOT_MSG = "Must be run from the root of a git repository"
GIT_REPO_NON_BARE_MSG = "Running in a bare repository is not supported"

RE_RUN_INIT_MSG = (
    "Re-running `init` is not currently supported - please use the `config` and `update` commands"
)
RE_RUN_DIRTY_MSG = (
    "Running this command is not supported in non-initialised project - please run `init` first"
)


class Command(ABC):
    def __init__(self, force_config_repo_version: Union[str, None] = None, **kwargs) -> None:

        self._check_in_git_repo()

        self._check_re_run()

        self._force_config_repo_version = force_config_repo_version

        self._get_repo_manager_config()

        self._setup_config_repo(force_config_repo_version)

    @staticmethod
    def _check_in_git_repo() -> None:
        """Check if running from the root of a valid git repository

        Raises:
            GitRepositoryError if the current directory is not the root of a valid git repo.
        """
        current_dir = Path.getcwd()

        try:
            repo = Repo(current_dir)
        except InvalidGitRepositoryError:
            raise GitRepositoryError(GIT_REPO_NOT_ROOT_MSG)

        if repo.bare:
            raise GitRepositoryError(GIT_REPO_NON_BARE_MSG)

    @abstractmethod
    def _check_re_run(self) -> None:
        """Check if the command is running in an already initialised repository

        The concrete implementation needs to decide what to do if the repo has or hasn't been
        initialised.
        """

    def _get_repo_manager_config(self) -> None:

        self.repo_manager_config = get_config(False)

    def _setup_config_repo(self, force_config_repo_version: Union[str, None] = None) -> None:

        self.config_repo = get_config_repo()

        # Pick config state to use
        if force_config_repo_version is None:

            versions = self.config_repo.list_versions()

            self.chosen_version = versions[0]
        else:
            self.chosen_version = force_config_repo_version

        # Checkout required version
        self.config_repo.checkout_version(self.chosen_version)

    def _resolve_profiles(self) -> None:

        self.profiles = ["all"] + self.repo_manager_config["profiles"]

        return self.profiles


class InitCommand(Command):
    def _check_re_run(self) -> None:
        """Check if the command is running in an already initialised repository

        Raises:
            RerunError if the repository has already been initialised with repo-manager.
        """

        if config_exists():
            raise RerunError(RE_RUN_INIT_MSG)

    def _get_repo_manager_config(self) -> None:

        # Override to create config file
        self.repo_manager_config = get_config(True)

    def run(self) -> None:

        ConfigCommand(self._force_config_repo_version).run()

        return UpdateCommand(self._force_config_repo_version).run()


class ConfigCommand(Command):
    # force_config_repo_version only intended for use by Init command, not direct CLI
    def __init__(self, force_config_repo_version: Union[str, None] = None) -> None:

        force_config_repo_version = force_config_repo_version or state_manager.state["config"].get(
            "installed_version"
        )

        super().__init__(force_config_repo_version=force_config_repo_version)

        all_profile_name: List[str] = self.config_repo.get_all_profile_names()

        self.available_profiles = self.config_repo.get_profile_configs(all_profile_name)

    def _check_re_run(self) -> None:
        """Check if the command is running in an already initialised repository

        Raises:
            RerunError if the repository has not been initialised with repo-manager yet.
        """
        if not config_exists():
            raise RerunError(RE_RUN_DIRTY_MSG)

    def run(self) -> None:

        selected_profile_names = self._prompt_user_select_profiles()

        self.repo_manager_config["profiles"] = selected_profile_names

        save_config(self.repo_manager_config)

    def _prompt_user_select_profiles(
        self,
    ) -> List[str]:

        profile_groups = self.config_repo.get_group_config()
        selected_profiles = self.repo_manager_config["profiles"]

        # Do not render "all" profile
        filtered_available_profiles = [
            profile for profile in self.available_profiles if profile["name"] != "all"
        ]

        try:

            return ProfileSelection(
                filtered_available_profiles, profile_groups, selected_profiles
            ).select_profiles()
        except NotSupportedOnPythonVersion:
            secho("Interactive profile selection is not available on python <3.7.\n")
            secho("You can edit profiles manually in .repo-manager/config.yml.\n")
            secho()

            # Return originally selected profiles
            return selected_profiles


class UpdateCommand(Command):
    def _check_re_run(self) -> None:
        """Check if the command is running in an already initialised repository

        Raises:
            RerunError if the repository has not been initialised with repo-manager yet.
        """
        if not config_exists():
            raise RerunError(RE_RUN_DIRTY_MSG)

    def run(self) -> None:

        # FIXME refactor below code

        self._resolve_profiles()

        config_build_sets: DefaultDict[str, List[Path]] = self._get_config_build_sets()

        self._handle_bootstrap_files(config_build_sets)

        # FIXME try/finally delete previous state
        try:
            shutil.move(CONFIGS_STATE_PATH, PREVIOUS_CONFIGS_STATE_PATH)
        except FileNotFoundError:
            pass

        os.makedirs(CONFIGS_STATE_PATH, exist_ok=True)
        os.makedirs(MERGING_CONFIGS_PATH, exist_ok=True)

        failed_merges = self._merge_config_files(config_build_sets)

        try:
            shutil.rmtree(PREVIOUS_CONFIGS_STATE_PATH)
        except FileNotFoundError:
            pass

        try:
            shutil.rmtree(MERGING_CONFIGS_PATH)
        except FileNotFoundError:
            pass

        if failed_merges:
            secho("Failed to generate the following files due to outside changes:\n")
            secho("\n".join(f"    {f}" for f in failed_merges), fg=colors.YELLOW)
            secho()
            # FIXME return non-zero

        # Set current state
        state_manager.state["config"]["installed_version"] = self.chosen_version
        state_manager.state["config"]["installed_config"] = self.repo_manager_config
        state_manager.state["config"]["failed_merges"] = failed_merges

    def _get_config_build_sets(self) -> DefaultDict[str, List[Path]]:
        """Get set of config files to be merged based on selected profiles"""

        exclude_files = self.repo_manager_config.get("exclude_files", [])

        config_build_sets: DefaultDict[str, List[Path]] = defaultdict(list)

        # Gather config files from reference repo
        selected_profiles_config_files = self.config_repo.list_config_files(self.profiles)

        for profile, profile_config_file_paths in selected_profiles_config_files.items():

            for relative_config_path in profile_config_file_paths:

                target_path = _reduce_relative_path(relative_config_path)

                if target_path in exclude_files:
                    continue

                config_path = self.config_repo.get_config_path(profile, relative_config_path)
                config_build_sets[target_path].append(config_path)

        return gather_local_files(config_build_sets)

    @staticmethod
    def _handle_bootstrap_files(config_build_sets: DefaultDict[str, List[Path]]) -> None:
        """Copy bootstrap files into place and remove them from the config build sets passed in"""

        for config_path_key, paths in deepcopy(config_build_sets).items():

            # Get filename
            filename = os.path.basename(config_path_key)

            if filename.startswith(BOOTSTRAP_PREFIX):

                # Check just one file and remove from config list
                # FIXME general error handling for CLI
                assert len(paths) == 1  # noqa B101 adds some defense to immature code
                del config_build_sets[config_path_key]

                destination_path = config_path_key.replace(BOOTSTRAP_PREFIX, "")

                # Add file if doesn't already existing
                if not os.path.exists(destination_path):
                    _copy_mkdirs(paths[0], destination_path)

    def _merge_config_files(self, config_build_sets: DefaultDict[str, List[Path]]) -> List[str]:
        """
        Compute the final merged file for each given target file path, write file if not present

        First build all merged files based on current settings.
        NOTE: Excluded files will not be built as they are not in config_build_sets.
        Then check if the current file content has diverged from the expected file content.
        If the current and expected content do not match, the merge is considered failed.

        Args:
            config_build_sets: A dict mapping the target file path to the list of files that should
                be merged.

        Returns:
            A list of file paths for which the merge was unsuccessful.
        """
        failed_merges = []

        for config_path_key, paths in config_build_sets.items():

            configmerger.verify_matching_extensions(paths)

            merging_file_path = MERGING_CONFIGS_PATH + config_path_key

            # Copy base file into repo
            _copy_mkdirs(paths[0], merging_file_path)

            # Check if merge handler is needed
            if len(paths) > 1:
                base_handler = configmerger.get_handler(merging_file_path)

                for path in paths[1:]:

                    merge_handler = configmerger.get_handler(path)

                    base_handler.merge(merge_handler)

            skip_existing_check = False

            if not os.path.exists(config_path_key):
                skip_existing_check = True

            if not skip_existing_check and not self._ready_to_replace(config_path_key):
                failed_merges.append(config_path_key)
                continue

            # Copy file to repo and state directory
            _copy_mkdirs(merging_file_path, config_path_key)

            # Update state file copy
            _copy_mkdirs(merging_file_path, CONFIGS_STATE_PATH + config_path_key)

        return failed_merges

    @staticmethod
    def _ready_to_replace(file_path: str) -> bool:
        """Check if the file has diverged from it's previous (or target) state

        Args:
            file_path: Relative path to the file to be checked.

        Returns:
            True if the file content is identical with the previous (or target) version.
            False otherwise.
        """
        previous_config_path = PREVIOUS_CONFIGS_STATE_PATH + file_path

        try:
            if not filecmp.cmp(file_path, previous_config_path):
                _copy_mkdirs(previous_config_path, CONFIGS_STATE_PATH + file_path)
                return False

        except FileNotFoundError as exc:
            if previous_config_path in str(exc):
                # Previous file version not found either because the file has been excluded until
                # now or there was a problem with the state (e.g. a file has been deleted from the
                # project's state directory).
                # Use the newly merged file to determine if the content has diverged.
                if filecmp.cmp(file_path, MERGING_CONFIGS_PATH + file_path):
                    return True

            return False

        return True

        # Check if state is current version continue
        # FIXME does not currently account for new profiles added/removed
        # if state_manager.state["config"]["installed_version"] == latest_version:
        #    shutil.copy2(file_path, CONFIGS_STATE_PATH + file_path)
        #    continue


class BuildCommand(UpdateCommand):
    def __init__(self) -> None:

        installed_version = state_manager.state["config"].get("installed_version")

        super().__init__(force_config_repo_version=installed_version)

    def _check_re_run(self) -> None:
        """Check if the command is running in an already initialised repository

        Raises:
            RerunError if the repository has not been initialised with repo-manager yet or the state
            file is missing.
        """
        if not config_exists() or state_manager.first_run:
            raise RerunError(RE_RUN_DIRTY_MSG)


def _copy_mkdirs(source: str, destination: str) -> None:

    if os.path.dirname(destination):
        os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copy2(source, destination)


def _reduce_relative_path(path: str) -> str:

    return path.split("merge.")[-1]

import copy
from typing import List, MutableSequence, Sequence

from repomanager.configrepo import FIELD_NAME_GROUPS, Group, Profile
from repomanager.exceptions import NotSupportedOnPythonVersion
from repomanager.tui.profilestate import ProfileStateManager

DEFAULT_GROUP: Group = {
    "name": "default",
    "title": "Assorted Profiles",
}

TUI_SUPPORTED = True
try:
    from repomanager.tui.profileselectiontextualapp import ProfileSelectionTextualApp

except ModuleNotFoundError:
    TUI_SUPPORTED = False


class ProfileSelection:
    def __init__(
        self,
        available_profiles: Sequence[Profile],
        groups: MutableSequence[Group],
        selected_profiles: List[str],
    ) -> None:

        if not TUI_SUPPORTED:
            raise NotSupportedOnPythonVersion

        self._available_profiles = available_profiles
        self._init_groups(groups)
        self._initially_selected_profiles = selected_profiles

        self.profile_state_manager = ProfileStateManager(
            self._available_profiles, self._initially_selected_profiles
        )

        self.textual_app = ProfileSelectionTextualApp(
            _sort_profiles_into_groups(self._groups, self._available_profiles),
            self.profile_state_manager,
        )

    def _init_groups(self, groups: MutableSequence[Group]) -> None:
        """Ensures the default group is included."""

        self._groups = copy.deepcopy(groups)

        found_default_group = False
        for group in self._groups:
            if group["name"] == DEFAULT_GROUP["name"]:
                found_default_group = True

        if not found_default_group:
            self._groups.append(DEFAULT_GROUP)

    def select_profiles(self) -> List[str]:

        self.textual_app.run()

        if self.textual_app.exist_status_save:
            return self.profile_state_manager.get_selected()
        else:
            return self._initially_selected_profiles


def _sort_profiles_into_groups(
    groups_arg: Sequence[Group],
    profiles: Sequence[Profile],
) -> Sequence[Group]:

    groups = copy.deepcopy(groups_arg)

    for group in groups:
        group["profiles"] = []

    for profile in profiles:

        profile_groups = profile.get(FIELD_NAME_GROUPS, [DEFAULT_GROUP["name"]])

        for profile_group in profile_groups:
            for group in groups:
                if group["name"] != profile_group:
                    continue

                group["profiles"].append(profile)

    return groups

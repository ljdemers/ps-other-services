from typing import List, Sequence

from repomanager.configrepo import Profile
from repomanager.exceptions import ProgrammaticError


class ProfileStateUIInterface:
    def set_selected(self, selected: bool) -> None:
        """Update UI with profile selection state"""
        raise NotImplementedError

    def set_locked(self, locked: bool) -> None:
        """Update UI with profile locked (selected but disabled)"""
        raise NotImplementedError


class ProfileStateManager:
    def __init__(
        self, profiles: Sequence[Profile], initially_selected_profiles: Sequence[str]
    ) -> None:

        self._profiles = profiles
        self._initially_selected_profiles = initially_selected_profiles

        self._init_profiles()

        self._connect_profile_states()

    def _init_profiles(self) -> None:

        self.profile_states = {}

        for profile in self._profiles:

            profile_name = profile["name"]
            profile_selected = profile_name in self._initially_selected_profiles

            self.profile_states[profile_name] = ProfileState(profile, profile_selected)

    def _connect_profile_states(self) -> None:

        for _name, profile_state in self.profile_states.items():
            profile_state.connect_profiles(self)

    def get_selected(self) -> List[str]:

        selected = []

        for _name, profile_state in self.profile_states.items():
            if profile_state.selected:
                selected.append(profile_state.name)

        return selected


class ProfileState:
    def __init__(self, profile: Profile, selected: bool = False) -> None:

        self.name = profile["name"]
        self._profile = profile
        self.selected = selected

        self.locked_by = set()
        self._depends_on_profile_states = []
        self._ui_handlers = None

        self._lock_children(selected)

    def connect_profiles(self, profile_manager: ProfileStateManager) -> None:
        """Link to dependant profiles"""

        if self._ui_handlers is not None:
            raise ProgrammaticError("connect_profiles method must be called before UI handler set")

        for name in self._profile.get("depends_on", []):
            self._depends_on_profile_states.append(profile_manager.profile_states[name])

    def add_ui_handler(self, ui_handler: ProfileStateUIInterface) -> None:

        if self._ui_handlers is None:
            self._ui_handlers = []

        self._ui_handlers.append(ui_handler)

        self.set_selected(self.selected, force=True)
        self._call_ui_set_lock(bool(self.locked_by))

    def set_selected(self, selected: bool, force: bool = False) -> None:

        # Do not allow selection when
        if self.locked_by and selected:
            return

        if not force and (selected == self.selected):
            return

        self.selected = selected

        self._lock_children(selected)

        if not self._ui_handlers:
            return

        for ui_handler in self._ui_handlers:
            ui_handler.set_selected(self.selected)

    def _lock_children(self, locked: bool) -> None:

        for profile_state in self._depends_on_profile_states:

            if locked:
                profile_state.add_depend_lock(self.name)
            else:
                profile_state.remove_depend_lock(self.name)

    def _call_ui_set_lock(self, locked: bool) -> None:

        if not self._ui_handlers:
            return

        for ui_handler in self._ui_handlers:
            ui_handler.set_locked(locked)

    def add_depend_lock(self, profile_name: str) -> None:

        previously_locked = bool(self.locked_by)

        self.locked_by.add(profile_name)

        if previously_locked:
            return

        self._call_ui_set_lock(True)

        self._lock_children(True)

    def remove_depend_lock(self, profile_name: str) -> None:

        previously_locked = bool(self.locked_by)

        try:
            self.locked_by.remove(profile_name)
        except KeyError:
            return

        if self.locked_by or not previously_locked:
            return

        self._call_ui_set_lock(False)

        self._lock_children(False)

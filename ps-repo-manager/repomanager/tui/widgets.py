from contextlib import suppress
from typing import Any, Callable, Dict, List, Sequence, Union

from textual.app import ComposeResult
from textual.widgets import Checkbox, Static

from repomanager.configrepo import Group
from repomanager.tui.profilestate import ProfileState, ProfileStateManager, ProfileStateUIInterface


class Text(Static):
    pass


class ProfileGroupSelection(Static):
    def __init__(
        self,
        groups: Sequence[Group],
        profile_state_manager: ProfileStateManager,
    ) -> None:

        self._groups = groups
        self._profile_state_manager = profile_state_manager

        super().__init__()

    def compose(self) -> ComposeResult:

        for group in self._groups:

            yield ProfileGroup(
                group["profiles"],
                group["name"],
                group["title"],
                group.get("description"),
                self._profile_state_manager,
            )


class ProfileGroup(Static):
    def __init__(
        self,
        profiles: List[Dict[str, Any]],
        group_key: str,
        group_title: str,
        group_description: Union[str, None],
        profile_state_manager: ProfileStateManager,
    ) -> None:

        self._profiles = profiles
        self._group_title = group_title
        self._group_description = group_description
        self._profile_state_manager = profile_state_manager

        super().__init__()

    def compose(self) -> ComposeResult:
        class ProfileGroupDescription(Text):
            pass

        class ProfileGroupTitle(Text):
            pass

        yield ProfileGroupTitle(self._group_title)

        if self._group_description:
            yield ProfileGroupDescription(self._group_description)

        for profile in self._profiles:

            yield ProfileWidget(
                profile["name"],
                profile.get("description", ""),
                self._profile_state_manager.profile_states[profile["name"]],
            )


class ProfileWidget(Static, ProfileStateUIInterface):
    def __init__(self, name: str, description: str, profile_state: ProfileState) -> None:

        self._profile_name = name
        self._profile_description = description
        self._profile_state = profile_state

        self._selected = False
        self._locked = False

        self._profile_state.add_ui_handler(self)

        super().__init__()

        self._lockable_checkbox = LockableCheckbox(
            self._selected, self._locked, self.checkbox_changed
        )

    def checkbox_changed(self, selected: bool) -> None:

        self._profile_state.set_selected(selected)

    def set_selected(self, selected: bool) -> None:

        self._selected = selected

        with suppress(AttributeError):
            self._lockable_checkbox.set_selected(selected)

    def set_locked(self, locked: bool) -> None:

        self._locked = locked

        with suppress(AttributeError):
            self._lockable_checkbox.set_locked(locked)

    def compose(self) -> ComposeResult:
        class ProfileName(Text):
            pass

        class ProfileDescription(Text):
            pass

        yield self._lockable_checkbox
        yield ProfileName(self._profile_name)
        yield ProfileDescription(self._profile_description)


class LockableCheckbox(Static):
    class LockedCheckbox(Static):
        def compose(self) -> ComposeResult:

            yield Static()

    def __init__(self, selected: bool, locked: bool, checked_change: Callable) -> None:

        self.selected = selected
        self.locked = locked
        self._checked_change = checked_change

        super().__init__()

        self._checkbox = Checkbox(selected, animate=False)
        self._checkbox_locked = LockableCheckbox.LockedCheckbox()

        self.set_locked(self.locked)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:

        self._checked_change(bool(event.value))

    def set_selected(self, selected: bool) -> None:

        self._checkbox.value = selected

    def set_locked(self, locked: bool) -> None:

        self.locked = locked

        self._checkbox.set_class(self.locked, "hidden")
        self._checkbox_locked.set_class(not self.locked, "hidden")

    def compose(self) -> ComposeResult:

        yield self._checkbox
        yield self._checkbox_locked

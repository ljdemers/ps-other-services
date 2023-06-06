import sys
from unittest import mock

import pexpect
import pytest

import repomanager.tui
from repomanager.exceptions import NotSupportedOnPythonVersion, ProgrammaticError
from repomanager.tui import DEFAULT_GROUP, ProfileSelection, _sort_profiles_into_groups
from repomanager.tui.profilestate import ProfileState, ProfileStateManager, ProfileStateUIInterface


@pytest.mark.skipif(
    sys.version_info >= (3, 7), reason="This test verified behaviour on python <3.8"
)
def test_python_unsupported():

    with pytest.raises(NotSupportedOnPythonVersion):
        ProfileSelection([], {"groups": {}}, [])


@pytest.mark.skipif(sys.version_info < (3, 7), reason="TUI not support in <3.7")
def test_ProfileSelection_init_python_supported():

    profile_selection = ProfileSelection(available_profiles=[], groups=[], selected_profiles=[])

    # Should at least contain the default group.
    assert DEFAULT_GROUP in profile_selection._groups


@pytest.mark.skipif(sys.version_info < (3, 7), reason="TUI not support in <3.7")
def test_ProfileSelection_init_with_groups_python_supported():

    fake_groups = [
        {
            "name": "fake-group-1",
            "title": "Fake Group 1",
        }
    ]

    profile_selection = ProfileSelection(
        available_profiles=[], groups=fake_groups, selected_profiles=[]
    )

    # Should contain the given groups and the default group.
    assert profile_selection._groups == fake_groups + [DEFAULT_GROUP]


@mock.patch.object(repomanager.tui, "ProfileSelectionTextualApp")
@pytest.mark.skipif(sys.version_info < (3, 7), reason="TUI not support in <3.7")
def test_tui_called(mock_textual_app):

    mock_textual_app.return_value.exist_status_save = False

    fake_selected_profiles = ["existing-profile"]

    profiles = ProfileSelection(
        available_profiles=[],
        groups=[],
        selected_profiles=fake_selected_profiles,
    ).select_profiles()

    mock_textual_app.assert_called()
    mock_textual_app.return_value.run.assert_called()

    assert profiles == fake_selected_profiles


@pytest.mark.skipif(sys.version_info < (3, 7), reason="TUI not support in <3.7")
def test_tui_abort():

    # FIXME extend to support basic selection scenarios (parameterised test)
    # Output to json to enable more advanced assertion after

    tui_expect = pexpect.spawn(
        """python -c "from repomanager.tui import ProfileSelection; import time; """
        """result = ProfileSelection(available_profiles=[], groups=[], selected_profiles=['already_selected']).select_profiles();"""
        """print('wait for me'); """
        """time.sleep(2); """
        """print(result)"""
    )

    tui_expect.expect("\\(a\\)bort")

    assert tui_expect.isalive()

    # Quit no selection
    tui_expect.send("a")

    tui_expect.expect("wait for me")

    output = tui_expect.read()

    assert "['already_selected']" in output.decode()


def test_sort_profiles_into_groups():

    repo_groups = [
        {
            "name": "high-level-profiles",
            "description": "These high level profiles meet most users needs...",
            "title": "High Level Profiles",
        },
        {
            "name": "add-ons",
            "description": "Profiles linked to technologies...",
            "title": "Add Ons",
        },
        {"name": "default", "title": "Assorted Profiles"},
    ]

    profiles = [
        {
            "name": "service_profile_a",
            "description": "Profile for service type A",
            "depends_on": [
                "profile_x",
                "profile_y",
            ],
            "groups": ["high-level-profiles"],
        },
        {
            "name": "library_profile",
            "description": "Profile for publishing a profile",
            "depends_on": ["profile_z"],
            "groups": ["high-level-profiles", "add-ons"],
        },
        {"name": "profile_x", "groups": ["add-ons"]},
        {"name": "profile_y", "description": "Profile Y..."},
    ]

    sorted_groups = _sort_profiles_into_groups(repo_groups, profiles)

    assert sorted_groups == [
        {
            **repo_groups[0],
            "name": "high-level-profiles",  # Explicit value here for clarity
            "profiles": [
                {
                    **profiles[0],
                    "name": "service_profile_a",  # Explicit value here for clarity
                },
                {
                    **profiles[1],
                    "name": "library_profile",
                },
            ],
        },
        {
            **repo_groups[1],
            "name": "add-ons",  # Explicit value here for clarity
            "profiles": [
                {
                    "name": "library_profile",
                    **profiles[1],
                },
                {
                    "name": "profile_x",
                    **profiles[2],
                },
            ],
        },
        {
            **repo_groups[2],
            "name": "default",  # Explicit value here for clarity
            "profiles": [
                {
                    "name": "profile_x",
                    **profiles[3],
                }
            ],
        },
    ]


MockProfileStateUI = lambda: mock.MagicMock(ProfileStateUIInterface)


def test_ProfileState_connect_profiles_order():
    """connect_profiles must be run before ui_profile"""

    profile_state = ProfileState({"name": "dummy"})

    profile_state.add_ui_handler(MockProfileStateUI())

    with pytest.raises(ProgrammaticError):

        profile_state.connect_profiles(None)


def test_ProfileState_set_selected():

    profile_state = ProfileState({"name": "dummy"})

    ui = MockProfileStateUI()

    profile_state.add_ui_handler(ui)

    add_handle_count = ui.set_selected.call_count

    # Check call count within reason, don't care exact amount
    assert 0 < add_handle_count < 5

    profile_state.set_selected(True)

    set_selected_count = ui.set_selected.call_count - add_handle_count

    # Check call count within reason, don't care exact amount
    assert 0 < set_selected_count < 5


@pytest.mark.parametrize("already_selected", (True, False))
def test_ProfileState_add_ui_handler(already_selected):

    profile_state_manager = ProfileStateManager(
        [
            {
                "name": "depends_on_top",
                "depends_on": [
                    "depends_on_1",
                    "depends_on_2",
                ],
            },
            {
                "name": "depends_on_1",
            },
            {
                "name": "depends_on_2",
            },
        ],
        ["depends_on_top"] if already_selected else [],
    )

    top_profile = profile_state_manager.profile_states["depends_on_top"]

    bottom_profile_1 = profile_state_manager.profile_states["depends_on_1"]
    bottom_profile_2 = profile_state_manager.profile_states["depends_on_2"]

    top_ui_1 = MockProfileStateUI()
    top_ui_2 = MockProfileStateUI()

    top_profile.add_ui_handler(top_ui_1)
    top_profile.add_ui_handler(top_ui_2)

    top_ui_1.set_selected.assert_called_with(already_selected)
    top_ui_2.set_selected.assert_called_with(already_selected)
    top_ui_1.set_selected.reset_mock()
    top_ui_2.set_selected.reset_mock()

    top_ui_1.set_locked.assert_called_with(False)
    top_ui_2.set_locked.assert_called_with(False)
    top_ui_1.set_selected.reset_mock()
    top_ui_2.set_selected.reset_mock()

    bottom_ui_1 = MockProfileStateUI()
    bottom_ui_2 = MockProfileStateUI()

    bottom_profile_1.add_ui_handler(bottom_ui_1)
    bottom_profile_2.add_ui_handler(bottom_ui_2)

    bottom_ui_1.set_selected.assert_called_with(False)
    bottom_ui_2.set_selected.assert_called_with(False)
    bottom_ui_1.set_selected.reset_mock()
    bottom_ui_2.set_selected.reset_mock()

    bottom_ui_1.set_locked.assert_called_with(already_selected)
    bottom_ui_2.set_locked.assert_called_with(already_selected)
    bottom_ui_1.set_selected.reset_mock()
    bottom_ui_2.set_selected.reset_mock()

    top_profile.set_selected(not already_selected)

    top_ui_1.set_selected.assert_called_with(not already_selected)
    top_ui_2.set_selected.assert_called_with(not already_selected)

    bottom_ui_1.set_locked.assert_called_with(not already_selected)
    bottom_ui_2.set_locked.assert_called_with(not already_selected)


def test_ProfileState_add_depend_lock():

    profile_state = ProfileState({"name": "dummy"}, True)

    ui = MockProfileStateUI()
    profile_state.add_ui_handler(ui)

    ui.set_locked.assert_called_with(False)
    ui.reset_mock()

    assert not profile_state.locked_by

    # Add Lock
    profile_state.add_depend_lock("lock1")

    ui.set_locked.assert_called_with(True)
    ui.reset_mock()

    assert profile_state.locked_by

    # Add Lock again
    profile_state.add_depend_lock("lock2")

    ui.set_locked.assert_not_called()

    assert profile_state.locked_by == {"lock1", "lock2"}

    # Remove()
    profile_state.remove_depend_lock("lock1")

    ui.set_locked.assert_not_called()

    assert profile_state.locked_by == {"lock2"}

    # Remove lock that doesn't exist
    profile_state.remove_depend_lock("lock1")

    ui.set_locked.assert_not_called()

    assert profile_state.locked_by == {"lock2"}

    # Remove last lock
    profile_state.remove_depend_lock("lock2")

    ui.set_locked.assert_called_with(False)
    ui.reset_mock()

    assert not profile_state.locked_by

    # Add Lock again
    profile_state.add_depend_lock("lock1")

    ui.set_locked.assert_called_with(True)
    ui.reset_mock()

    assert profile_state.locked_by


def test_ProfileState_connect_profiles_no_depends():

    profile_state_manager = ProfileStateManager([{"name": "dummy"}], [])

    profile_state = profile_state_manager.profile_states["dummy"]

    profile_state.connect_profiles(profile_state_manager)

    ui = MockProfileStateUI()

    profile_state.add_ui_handler(ui)

    ui.set_selected.assert_called()


def test_ProfileState_connect_profiles():

    profile_state_manager = ProfileStateManager(
        [
            {
                "name": "depends_on_top",
                "depends_on": [
                    "depends_on_1",
                    "depends_on_2",
                ],
            },
            {
                "name": "depends_on_1",
            },
            {
                "name": "depends_on_2",
            },
        ],
        [],
    )

    profile_state_top = profile_state_manager.profile_states["depends_on_top"]
    profile_state_depends_on_1 = profile_state_manager.profile_states["depends_on_1"]
    profile_state_depends_on_2 = profile_state_manager.profile_states["depends_on_2"]

    # Already being called by ProfileStateManager init
    # profile_state_top.connect_profiles(profile_state_manager)

    ui_top = MockProfileStateUI()
    ui_depends_on_1 = MockProfileStateUI()
    ui_depends_on_2 = MockProfileStateUI()

    profile_state_top.add_ui_handler(ui_top)
    profile_state_depends_on_1.add_ui_handler(ui_depends_on_1)
    profile_state_depends_on_2.add_ui_handler(ui_depends_on_2)

    ui_top.set_selected.assert_called_with(False)
    ui_top.set_selected.reset_mock()

    ui_depends_on_1.assert_not_called()
    ui_depends_on_2.assert_not_called()

    # Set selected
    profile_state_top.set_selected(True)

    ui_top.set_selected.assert_called_with(True)
    ui_top.set_selected.reset_mock()

    ui_depends_on_1.set_locked.assert_called_with(True)
    ui_depends_on_2.set_locked.assert_called_with(True)
    ui_depends_on_1.reset_mock()
    ui_depends_on_2.reset_mock()

    assert profile_state_depends_on_1.locked_by == {"depends_on_top"}
    assert profile_state_depends_on_2.locked_by == {"depends_on_top"}

    # Re-unset selected
    profile_state_top.set_selected(False)

    ui_top.set_selected.assert_called_with(False)

    ui_depends_on_1.set_locked.assert_called_with(False)
    ui_depends_on_2.set_locked.assert_called_with(False)

    assert not profile_state_depends_on_1.locked_by
    assert not profile_state_depends_on_2.locked_by


def test_ProfileStateManager_connect_profiles():

    profile_state_manager = ProfileStateManager(
        [
            {"name": "no_depends"},
            {
                "name": "depends_on_top",
                "depends_on": [
                    "depends_on_middle_1",
                    "depends_on_middle_2",
                ],
            },
            {
                "name": "depends_on_middle_1",
                "depends_on": ["depends_on_bottom_1", "depends_on_bottom_2"],
            },
            {"name": "depends_on_middle_2", "depends_on": ["depends_on_bottom_2"]},
            {"name": "depends_on_bottom_1", "depends_on": []},
            {"name": "depends_on_bottom_2", "depends_on": []},
        ],
        [],
    )

    no_profile = profile_state_manager.profile_states["no_depends"]

    top_profile = profile_state_manager.profile_states["depends_on_top"]

    middle_1_profile = profile_state_manager.profile_states["depends_on_middle_1"]
    middle_2_profile = profile_state_manager.profile_states["depends_on_middle_2"]

    bottom_1_profile = profile_state_manager.profile_states["depends_on_bottom_1"]
    bottom_2_profile = profile_state_manager.profile_states["depends_on_bottom_2"]

    # Connect mock UIs
    ui_no_profile = MockProfileStateUI()
    no_profile.add_ui_handler(ui_no_profile)

    ui_top_profile = MockProfileStateUI()
    top_profile.add_ui_handler(ui_top_profile)

    ui_middle_1 = MockProfileStateUI()
    middle_1_profile.add_ui_handler(ui_middle_1)

    ui_middle_2 = MockProfileStateUI()
    middle_2_profile.add_ui_handler(ui_middle_2)

    ui_bottom_1 = MockProfileStateUI()
    bottom_1_profile.add_ui_handler(ui_bottom_1)

    ui_bottom_2 = MockProfileStateUI()
    bottom_2_profile.add_ui_handler(ui_bottom_2)

    # Check all profiles called with no lock
    ui_no_profile.set_locked.assert_called_with(False)
    ui_no_profile.reset_mock()
    ui_top_profile.set_locked.assert_called_with(False)
    ui_top_profile.reset_mock()

    ui_middle_1.set_locked.assert_called_with(False)
    ui_middle_1.reset_mock()
    ui_middle_2.set_locked.assert_called_with(False)
    ui_middle_2.reset_mock()

    ui_bottom_1.set_locked.assert_called_with(False)
    ui_bottom_1.reset_mock()
    ui_bottom_2.set_locked.assert_called_with(False)

    # Should lock all children
    top_profile.set_selected(True)

    ui_no_profile.set_locked.assert_not_called()
    ui_top_profile.set_locked.assert_not_called()

    ui_middle_1.set_locked.assert_called_with(True)
    ui_middle_1.reset_mock()
    ui_middle_2.set_locked.assert_called_with(True)
    ui_middle_2.reset_mock()

    ui_bottom_1.set_locked.assert_called_with(True)
    ui_bottom_1.reset_mock()
    ui_bottom_2.set_locked.assert_called_with(True)
    ui_bottom_2.reset_mock()

    assert middle_1_profile.locked_by == {"depends_on_top"}
    assert middle_2_profile.locked_by == {"depends_on_top"}

    assert bottom_1_profile.locked_by == {"depends_on_middle_1"}
    assert bottom_2_profile.locked_by == {"depends_on_middle_1", "depends_on_middle_2"}

    # Should unlock all children
    top_profile.set_selected(False)

    ui_no_profile.set_locked.assert_not_called()
    ui_top_profile.set_locked.assert_not_called()

    ui_middle_1.set_locked.assert_called_with(False)
    ui_middle_1.reset_mock()
    ui_middle_2.set_locked.assert_called_with(False)
    ui_middle_2.reset_mock()

    ui_bottom_1.set_locked.assert_called_with(False)
    ui_bottom_1.reset_mock()
    ui_bottom_2.set_locked.assert_called_with(False)
    ui_bottom_2.reset_mock()

    assert not middle_1_profile.locked_by
    assert not middle_2_profile.locked_by

    assert not bottom_1_profile.locked_by
    assert not bottom_2_profile.locked_by

    # Lock middle 1 and 2
    middle_1_profile.set_selected(True)
    middle_2_profile.set_selected(True)

    ui_no_profile.set_locked.assert_not_called()
    ui_top_profile.set_locked.assert_not_called()

    ui_middle_1.set_locked.assert_not_called()
    ui_middle_2.set_locked.assert_not_called()

    ui_bottom_1.set_locked.assert_called_with(True)
    ui_bottom_1.reset_mock()
    ui_bottom_2.set_locked.assert_called_with(True)
    ui_bottom_2.reset_mock()

    assert not middle_1_profile.locked_by
    assert not middle_2_profile.locked_by

    assert bottom_1_profile.locked_by == {"depends_on_middle_1"}
    assert bottom_2_profile.locked_by == {"depends_on_middle_1", "depends_on_middle_2"}

    # Unlock middle 1
    middle_1_profile.set_selected(False)

    ui_no_profile.set_locked.assert_not_called()
    ui_top_profile.set_locked.assert_not_called()

    ui_middle_1.set_locked.assert_not_called()
    ui_middle_2.set_locked.assert_not_called()

    ui_bottom_1.set_locked.assert_called_with(False)
    ui_bottom_2.set_locked.assert_not_called()

    assert not middle_1_profile.locked_by
    assert not middle_2_profile.locked_by

    assert not bottom_1_profile.locked_by
    assert bottom_2_profile.locked_by == {"depends_on_middle_2"}

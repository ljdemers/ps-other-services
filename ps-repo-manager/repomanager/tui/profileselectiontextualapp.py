from typing import Sequence

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from repomanager.configrepo import Group
from repomanager.tui.profilestate import ProfileStateManager
from repomanager.tui.widgets import ProfileGroupSelection, Text


class ProfileSelectionTextualApp(App):

    BINDINGS = [
        ("s", "save", "(s)ave and quit"),
        ("a", "abort", "(a)bort changes"),
    ]

    CSS_PATH = "profile_selection_textual.css"

    TITLE = "repo-manager profile selection"

    def __init__(
        self,
        groups: Sequence[Group],
        profile_state_manager: ProfileStateManager,
    ) -> None:

        self._groups = groups
        self._profile_state_manager = profile_state_manager

        self.exist_status_save = False

        super().__init__()

    def compose(self) -> ComposeResult:
        class ProfileSelectionDescription(Text):
            pass

        yield Header()

        yield ProfileSelectionDescription(
            """
Here you can browse and then select profiles repo-manager will apply to your repo.

A profile is just a collection of files to be copied or merged in. Some files repo-manager will copy in once only (bootstrapping) and some files repo-manager will keep track of and provide means to update.

The profiles are grouped to aid selection and some profiles will also select other profiles.

You can navigate using your mouse or [bold]tab[/bold] (focus down), [bold]shift-tab[/bold] (focus up) and [bold]enter/space[/bold] to toggle selection. [bold]Arrow keys[/bold] scroll the page.
        """
        )

        yield ProfileGroupSelection(self._groups, self._profile_state_manager)

        yield Footer()

    def action_save(self) -> None:

        self.exist_status_save = True

        self.exit()

    def action_abort(self) -> None:

        self.exit()

from unittest import mock

from typer.testing import CliRunner

import repomanager.cli as cli_module
from repomanager.cli import app
from repomanager.exceptions import GitRepositoryError

runner = CliRunner(
    mix_stderr=False,  # Keep stdout and stderr separate.
)


FAKE_REPO_ERROR_MSG = "Repo Error"
RepoError = GitRepositoryError(FAKE_REPO_ERROR_MSG)


@mock.patch.object(cli_module, "InitCommand")
def test_init_success(mock_init_cmd):
    """Successfully run `init` command without additional parameters"""

    result = runner.invoke(app, ["init"])

    mock_init_cmd.assert_called_once_with(force_config_repo_version=None)
    mock_init_cmd.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "InitCommand")
def test_init_force_config_repo_version_success(mock_init_cmd):
    """Successfully run `init` command using specific config repo version"""

    test_config_repo_version = "1.2.3"

    result = runner.invoke(app, ["init", "--force-config-repo-version", test_config_repo_version])

    mock_init_cmd.assert_called_once_with(force_config_repo_version=test_config_repo_version)
    mock_init_cmd.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "InitCommand", side_effect=RepoError)
def test_init_raise_git_repo_error(mock_init_cmd):
    """Raise GitRepositoryError while running `init` command"""

    result = runner.invoke(app, ["init"])

    mock_init_cmd.assert_called_once_with(force_config_repo_version=None)
    mock_init_cmd.return_value.run.assert_not_called()

    assert result.exit_code == GitRepositoryError.exit_code
    assert FAKE_REPO_ERROR_MSG in result.stderr


@mock.patch.object(cli_module, "ConfigCommand")
def test_config_success(mock_config_cmd):
    """Successfully run `config` command without additional parameters"""

    result = runner.invoke(app, ["config"])

    mock_config_cmd.assert_called_once_with()
    mock_config_cmd.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "ConfigCommand", side_effect=RepoError)
def test_config_raise_git_repo_error(mock_config_cmd):
    """Raise GitRepositoryError while running `config` command"""

    result = runner.invoke(app, ["config"])

    mock_config_cmd.assert_called_once_with()
    mock_config_cmd.return_value.run.assert_not_called()

    assert result.exit_code == GitRepositoryError.exit_code
    assert FAKE_REPO_ERROR_MSG in result.stderr


@mock.patch.object(cli_module, "UpdateCommand")
def test_update_success(mock_update_cmd):
    """Successfully run `update` command without additional parameters"""

    result = runner.invoke(app, ["update"])

    mock_update_cmd.assert_called_once_with(force_config_repo_version=None)
    mock_update_cmd.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "UpdateCommand")
def test_update_force_config_repo_version_success(mock_update_cmd):
    """Successfully run `update` command using specific config repo version"""

    test_config_repo_version = "1.2.3"

    result = runner.invoke(app, ["update", "--force-config-repo-version", test_config_repo_version])

    mock_update_cmd.assert_called_once_with(force_config_repo_version=test_config_repo_version)
    mock_update_cmd.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "UpdateCommand", side_effect=RepoError)
def test_update_raise_git_repo_error(mock_update_cmd):
    """Raise GitRepositoryError while running `update` command"""

    result = runner.invoke(app, ["update"])

    mock_update_cmd.assert_called_once_with(force_config_repo_version=None)
    mock_update_cmd.return_value.run.assert_not_called()

    assert result.exit_code == GitRepositoryError.exit_code
    assert FAKE_REPO_ERROR_MSG in result.stderr


@mock.patch.object(cli_module, "BuildCommand")
def test_build_success(mock_build):
    """Successfully run `build` command without additional parameters"""

    result = runner.invoke(app, ["build"])

    mock_build.assert_called_once_with()
    mock_build.return_value.run.assert_called_once_with()

    assert result.exit_code == 0
    assert not result.stderr


@mock.patch.object(cli_module, "BuildCommand", side_effect=RepoError)
def test_build_raise_git_repo_error(mock_build_cmd):
    """Raise GitRepositoryError while running `build` command"""

    result = runner.invoke(app, ["build"])

    mock_build_cmd.assert_called_once_with()
    mock_build_cmd.return_value.run.assert_not_called()

    assert result.exit_code == GitRepositoryError.exit_code
    assert FAKE_REPO_ERROR_MSG in result.stderr

"""Repo Manager specific exceptions

Inheriting from `ClickException` will make Click (which Typer is built on) handle the exception
automatically.

For more information see: https://click.palletsprojects.com/en/latest/exceptions/

See here for available sub-classes:
https://click.palletsprojects.com/en/latest/exceptions/#which-exceptions-exist
"""
from click import UsageError


class RepoManagerException(Exception):
    """Base class for Repo Manager specific exception"""


class ProgrammaticError(RepoManagerException):
    """Condition reached that suggests error in code"""


class ConfigRepoError(RepoManagerException, UsageError):
    """Raise if there is a problem with the config repo"""


class GitRepositoryError(RepoManagerException, UsageError):
    """Raise if there is a problem with the underlying git repository"""


class RerunError(RepoManagerException, UsageError):
    """Raise if there is a problem when re-running commands in a repo"""


class NotSupportedOnPythonVersion(RepoManagerException):
    """Raise when feature not supported on current python version"""


class ConfigurationValidationError(RepoManagerException, UsageError):
    """Raise if the given configuration couldn't be validated"""

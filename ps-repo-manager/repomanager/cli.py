from typing import Union

from typer import Typer

from repomanager.commands import BuildCommand, ConfigCommand, InitCommand, UpdateCommand

app = Typer()


@app.command()
def init(force_config_repo_version: Union[str, None] = None) -> None:
    """
    Setup repo to use repo-manager and run initial update.
    """
    InitCommand(force_config_repo_version=force_config_repo_version).run()


@app.command()
def config() -> None:
    """Run profile selection"""
    ConfigCommand().run()


@app.command()
def check() -> None:
    """
    Check for valid configuration and whether files managed by repo-manager are as it expects - i.e. haven't been edited
    """
    raise NotImplementedError


@app.command()
def build() -> None:
    """Build files managed by repo-manager using the current version of configs

    This command will not update the config repository to the latest version available.
    """
    BuildCommand().run()


@app.command()
def update(force_config_repo_version: Union[str, None] = None) -> None:
    """
    Pull in latest config version from config repo and run build.
    """
    UpdateCommand(force_config_repo_version=force_config_repo_version).run()


if __name__ == "__main__":
    app()

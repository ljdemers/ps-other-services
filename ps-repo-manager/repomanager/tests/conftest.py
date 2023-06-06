import os
import pathlib
import random
import string
import tempfile

import git
import pytest

from repomanager.utils import yaml_dump


def _create_file_directory(base_path, name, definition):

    # Determine record type
    file_extension = pathlib.Path(name).suffix

    new_path = pathlib.Path(base_path) / pathlib.Path(name)

    # Directory
    if not file_extension:
        pathlib.Path(new_path).mkdir(parents=True, exist_ok=False)

        if "files" in definition:
            for child_name, child_definition in definition["files"].items():
                _create_file_directory(new_path, child_name, child_definition)

    elif file_extension in (".yml", ".yaml"):
        with open(new_path, "w") as file_object:
            yaml_dump(definition["data"], file_object)
    else:
        with open(new_path, "w") as file_object:
            file_object.write(definition["data"])


@pytest.fixture
def fake_repo():

    with tempfile.TemporaryDirectory() as temp_repo:

        def _fake_repo(repo_spec):

            repo_directory = pathlib.Path(temp_repo) / pathlib.Path(
                "".join(
                    random.choices(  # noqa B311 test logic
                        string.ascii_uppercase + string.digits, k=10
                    )
                )
            )
            repo_directory.mkdir(parents=True, exist_ok=False)

            git.Repo.init(repo_directory)

            for name, definition in repo_spec.items():

                _create_file_directory(repo_directory, name, definition)

            return repo_directory

        yield _fake_repo


@pytest.fixture
def temp_dir_chdir():

    original_dir = os.getcwd()

    with tempfile.TemporaryDirectory() as temp_repo:

        os.chdir(temp_repo)

        yield temp_repo

    os.chdir(original_dir)

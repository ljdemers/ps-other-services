import path  # Note this is not pathlib

from repomanager.localfiles import gather_local_files


def test_gather_local_files(fake_repo):

    repo_path = fake_repo(
        {
            "nested": {"files": {"merge.test.yml": {"data": {"test": "hello"}}}},
            "merge.root-test.yml": {"data": {"test": "hello"}},
            "root-test.yml.merge": {"data": "test: hellow"},
        }
    )

    # Change to temp dir
    with path.Path(repo_path):

        updated_config = gather_local_files(
            {"nested/test.yml": ["nested/test.yml"], "root-test.yml": ["root-test.yml"]}
        )

        assert updated_config == {
            "nested/test.yml": ["nested/test.yml", "nested/merge.test.yml"],
            "root-test.yml": ["root-test.yml", "merge.root-test.yml", "root-test.yml.merge"],
        }

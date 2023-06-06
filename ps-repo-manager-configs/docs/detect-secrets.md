# detect-secrets

Every time `detect-secrets` gets updated to a newer version,
it's necessary to update the "empty" `.secrets.baseline` file as well.

That file is distributed as `profiles/all/bootstrap..secrets.baseline`
and will be rendered into the project directory as `.secrets.baseline`.

To generate an updated version of the `.secrets.baseline` file,
ensure your local installation of `detect-secrets` matches the one in `profiles/all/.pre-commit-config.yaml`,
e.g. (ideally inside a virtual environment):

```
pip install "detect-secrets==v1.2.0"
```

then run the following command from the top level directory of your local `ps-repo-manager-configs` repository:

```
detect-secrets scan --exclude-files "(package.lock.json|.*tests.*|.*test_.*|.*alembic.*)" > profiles/all/bootstrap..secrets.baseline
```

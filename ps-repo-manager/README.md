# repo-manager

## Installation

### Pre-requisites

These *should* be setup for every developer already.

- github access to `Pole-Star-Space-Applications-USA/ps-repo-manager`
  and `Pole-Star-Space-Applications-USA/ps-repo-manager-config`
- [AWS CLI V2 Installation Guide][aws_cli_docs_ps]
- polestar-tools AWS CLI profile setup

### Install Script

From anywhere on your system run:

```
git clone --depth 1 --branch main git@github.com:Pole-Star-Space-Applications-USA/ps-repo-manager.git /tmp/repo-manager && bash /tmp/repo-manager/bin/install.sh; rm -rf /tmp/repo-manager
```
> **Note**:
> The `install.sh` script will retrieve an AWS CodeArtifact token via the AWS CLI and use it to `pip install` the latest published version of repo-manager from AWS CodeArtifact.

### Installing Python 3.6 [Temporary Workaround for Python Projects]

> **Note**:
> Due to an [issue with `poetry-core` in isort][isort_issue_2077] and
> with our current requirement to support tools that run on Python 3.6,
> it is not possible to update `isort` to a newer version.
> The current workaround for this is to force Python 3.6 when running the `isort` pre-commit hook.
> In order for this to work,
> it is necessary to have Python 3.6 installed on the system running the pre-commit hooks.
> *If* your project requires the `python` profile
> (see [Profile Selection section](#profile-selection)),
> please follow the steps below to make Python 3.6 available on your system
> (assuming Ubuntu 22.04, please see official installation instructions for other operating systems).

* Check your system Python version, e.g.:
  ```
  $ python --version
  Python 3.10.6
  ```

* [Install][pyenv_installation] `pyenv` (Simple Python Version Management):
  ```
  curl https://pyenv.run | bash
  ```

* Follow the instructions to add exports to `~/.bashrc`, e.g.:
  ```
  echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
  echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
  echo 'eval "$(pyenv init -)"' >> ~/.bashrc
  ```

* Start a fresh terminal for the `pyenv` command to become available.

* Update `pyenv` to get all available versions:
  ```
  pyenv update
  ```

* Update system package information:
  ```
  sudo apt update
  ```

* Install [recommended][pyenv_recommended_ubuntu] system packages (Ubuntu):
  ```
  sudo apt install --yes \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    clang
  ```
  These are necessary in order to be able to compile Python 3.6 without errors and warnings.

* Use `pyenv` to install Python 3.6:
  ```
  CC=clang pyenv install 3.6.15
  ```

* Use `pyenv` to install your preferred Python version, e.g. the system version from above:
  ```
  pyenv install 3.10.6
  ```

* Make **both** versions available globally
  (the order of versions matters, the first will become the default Python version):
  ```
  pyenv global 3.10.6 3.6.15
  ```

* Check the main Python version:
  ```
  $ python --version
  Python 3.10.6
  ```

## Updating

You can update repo-manager by re-running the installation command above (i.e. copy and pasting the above line).
The `pip` installation command that gets run will also update existing installations.

## Introductory Media

### Intro and demo Dec 2022 (`0.7.0`)

Video:
https://drive.google.com/drive/folders/1iDoqejkzUR5tS9gBLKQWw_X1rLurxmCJ

Slides:
https://lucid.app/lucidchart/dd0c348f-8cbb-4db7-aaec-fb5ad5c3af1f/edit?viewport_loc=-831%2C-551%2C2708%2C1708%2C0_0&invitationId=inv_22bb1fec-dd51-4992-87ec-4c69f71b537a

## Usage

All commands below need to be run from the project that should be managed by repo-manager (must be a git repository).

### Initialisation

Initialise a project with the `init` command:

```
cd /path/to/repo
repo-manager init
```

This will generate a `.repomanager` directory, a repo-manager configuration file (`.repomanager/config.yml`),
launch the profile selection UI (also available later via the `config` command),
and then pull in the latest files for the selected profiles (see also `update` command).

### [Profile Selection](#profile-selection)

After a project has been initialised with repo-manager, it is possible to run:
```
repo-manager config
```
at any time to start the profile selection tool, and update the set of selected profiles.

The profile selection tool provides information on what each profile provides.
The profiles and descriptions are pulled from the `ps-repo-manager-configs` [repository][configs_profiles].

Some profiles have other profiles they depend on.
These profiles become "locked" once the parent profiles are selected and cannot be unselected.
E.g. the `java-library` profile which provides pipelines to publish Java libraries depends on the generic `java` profile that includes files needed for all Java projects.

You can also edit the profiles manually by specifying a list of profiles in the `profiles` field in `.repomanager/config.yml`.
If `profiles` is an empty list, or no profiles have been selected in the selection tool, only the `all` profile will be used.

### Profile Update

As the profiles defined in `ps-repo-manager-configs` may change
(updates to existing files in a profile, new files added to existing profiles, new profiles added, etc),
it is advisable to run:

```
repo-manager update
```

regularly in every project managed by repo-manager.

By default, the `update` command will pull in the latest release of `ps-repo-manager-configs`.

If new configuration is available for any of the profiles selected in a given project,
the files associated with those profiles will be updated automatically, along with some state stored in `.repomanager`.

> **Note**:
> Always review the changes after running the `update` command
> and commit them to your repository before further development.

### Merge Files

In the current implementation, repo-manager uses `merge.*` files
in order to manage _local_ changes to configuration files like `.pre-commit-config.yaml`.

This means, if you would like to for example add pre-commit hooks inside your own project
which don't exist in any of the profiles that repo-manager provides,
you can create a merge file called `merge..pre-commit-config.yaml`
(using the same syntax as a regular `.pre-commit-config.yaml` file)
and define the hooks there.

Then run:

```
repo-manager update
```

which will read all `merge.*` files and _merge_ their contents with that of the "base" files
defined in the corresponding profiles before writing it into the project directory.

> **Note**:
> Always review the changes after running the `update` command
> and commit them to your repository before further development.

#### Removing values

A `None` value for a key in a merge file will be interpreted as removal of that item.
When `None` is not available (e.g. TOML) the string `__repo-manager__None` can be used in its place.

### Help Guide

To launch the repo-manager help command run:

```
repo-manager --help
```

> **Note**:
> Additional help is available for the individual commands via e.g.:
> Using the command `repo-manager --help` and `repo-manager <command> --help`

## Reporting issues

Please reports bugs here:

https://pole-star-global.monday.com/boards/3039571698/views/71225491

Please ensure to tag the ticket with `#repo-manager` and `#bug` (assuming bug).

Please include as much information as possible to recreate, including:

system, e.g. `Ubuntu 22.04`
output of:
```
python --version
pip --version
aws --version
```


## Developing Profiles

If you pass `repo-manager update --force-config-repo-version=<ref>` it will use that ref to update your repo.
For example if you want to use a branch named `cool-new-feature` you can set `--force-config-repo-version=cool-new-feature`.

It is recommended when creating new files or editing existing ones for `repo-manager` to manage to use a test repo or the repo that the file will first be used in.

E.g. if working on linting rules or a new GitHub action file, get these files working in a dummy or real service/library repo first.

Once you have the generic file working and ready create a PR in `ps-repo-manager-configs` placing the file in an existing profile or creating a new profile directory.
You can then use the `--force-config-repo-version=<ref>` pointing to your PR branch to re-apply this file to your chosen repo.
If this is successful, request a review from the SRE team on the PR.

Once the code is merge and a tag applied (contact SRE team via Slack `#devops`) it is then available to all managed repos.

## Developing Repo-Manager

See [here][ps_dev_tools] for the required development tools and [here][ps_coding_standards] for company-wide coding guidelines.

### Pre-Commit

To instantiate **Pre-Commit** in your local repository run:

```
pre-commit install --install-hooks
```

> **Note**:
> `pre-commit` runs locally before commits are complete.
> We also have a GitHub action that runs `pre-commit` to catch any instances where the developer hasn't run pre-commit locally.

[aws_cli_docs_ps]: https://github.com/Pole-Star-Space-Applications-USA/ps-dev-guides/blob/master/doc/required-developer-tools/aws-cli.md "Pole Star AWS CLI documentation"
[isort_issue_2077]: https://github.com/PyCQA/isort/issues/2077 "isort issue poetry-core"
[pyenv_installation]: https://github.com/pyenv/pyenv#installation "pyenv Installation"
[pyenv_recommended_ubuntu]: https://github.com/pyenv/pyenv/wiki#suggested-build-environment "Recommended packages Ubuntu"
[configs_profiles]: https://github.com/Pole-Star-Space-Applications-USA/ps-repo-manager-configs/tree/main/profiles "Available repo-manager profiles"
[ps_dev_tools]: https://github.com/Pole-Star-Space-Applications-USA/ps-dev-guides/blob/master/doc/required-developer-tools/required-tools.md "Pole Star Development Tools"
[ps_coding_standards]: https://github.com/Pole-Star-Space-Applications-USA/ps-dev-guides/blob/master/doc/coding-standards/README.md "Pole Star Coding Standards"

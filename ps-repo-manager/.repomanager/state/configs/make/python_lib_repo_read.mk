SHELL := /bin/bash # FIXME needed? also in other make shared code
.PHONY: deploy

# FIXME move to own make file
PS_PYTHON_REPO_NAME=ps-python

python-lib-repo-read-help:

	@echo " == PYTHON LIBRARY REPO CMDS =="
	@echo ""
	@echo "  === Poetry CMDS ==="
	@echo "  poetry-load-credentials"
	@echo "  poetry-install"
	@echo "  poetry-update"
	@echo ""
	@echo "  === CODEARTIFACT Specific CMDS ==="
	@echo "  set-pip-extra-index-codeartifact-url"
	@echo "  reset-pip-extra-index"
	@echo "  reset-pip-main-index - main index no longer used"
	@echo ""

help:: python-lib-repo-read-help

set-pip-extra-index-codeartifact-url:
	pip config set global.extra-index-url https://aws:${CODEARTIFACT_TOKEN_LOCAL_CREDS}@polestar-tools-324252367609.d.codeartifact.us-east-1.amazonaws.com/pypi/${CODEARTIFACT_TOKEN_LOCAL_CREDS}/simple/

reset-pip-main-index:
	pip config unset global.index-url

reset-pip-extra-index:
	pip config unset global.extra-index-url

# Use set-pip-extra-index-codeartifact-url
pip-set-codeartifact-url:
	make set-pip-extra-index-codeartifact-url

poetry-codeartifact-load-pass-env:
	poetry config http-basic.${PS_PYTHON_REPO_NAME} aws $${CODEARTIFACT_TOKEN}

poetry-load-credentials:
	@CODEARTIFACT_TOKEN=${CODEARTIFACT_TOKEN_LOCAL_CREDS} \
	make poetry-codeartifact-load-pass-env

poetry-install: poetry-load-credentials
	poetry install

poetry-update: poetry-load-credentials
	poetry update

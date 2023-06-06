#!/usr/bin/env bash
EGGDIR="screening_api.egg-info"

if [ -d "$EGGDIR" ]; then
    rm -rf ${EGGDIR}
fi

# CodeArtifact integration
#pip config set global.index-url "https://aws:$CODEARTIFACT_AUTH_TOKEN@test-domain-178847878690.d.codeartifact.us-east-1.amazonaws.com/pypi/polestar-pypi-store/simple/"
pip config set global.extra-index-url "https://pypi.org/simple"

echo 'Building development egg'
pip install -r dependency_links.txt
pip wheel -r requirements.txt -r requirements_dev.txt
pip install --prefer-binary -e .
pip install --prefer-binary -r requirements_dev.txt

echo 'Applying migrations'
alembic -c ${INI_FILE} upgrade head

echo 'Starting'
"$@"  # execute command passed to script

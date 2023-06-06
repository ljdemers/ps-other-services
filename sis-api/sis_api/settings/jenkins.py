# pylint: disable=wildcard-import,unused-wildcard-import
from .docker import *


INSTALLED_APPS = list(INSTALLED_APPS) + [
    'django_jenkins',
]

# Django-Jenkins configuration.
# Run `manage.py jenkins` with this parameters:
# `--project-apps-tests` and `--enable-coverage`.
PROJECT_APPS = [
    'ships',
    'ports',
    'system',
]
PEP8_RCFILE = '.pep8rc'
COVERAGE_RCFILE = 'coverage.rc'
PYLINT_RCFILE = '.pylintrc'
JENKINS_TASKS = (
    # 'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_pep8',
)

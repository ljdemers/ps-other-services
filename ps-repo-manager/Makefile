.PHONY: help
.DEFAULT: help

DOCKER_COMPOSE_TEST_COMMAND=docker-compose -f infra/docker/docker-compose.tests.yml

# This target is needed to allow for the (local) help to be shown at the bottom.
# DO NOT EDIT OR REMOVE.
help::

# Add help descriptions of your project specific commands here.
# Use format: <command> - <description>
service-help:
	@echo "= Repo repeatable commands ="
	@echo ""
	@echo " == Tests =="
	@echo ""
	@echo " pr-tests - run all tests before a PR"
	@echo ""
	@echo "  === Docker based tests ==="
	@echo "  docker-tests - build, run and stop docker based tests"
	@echo "  docker-tests-build - build docker test images"
	@echo "  docker-tests-down - stop docker test instances"
	@echo "  docker-tests-run - run docker tests"
	@echo ""
	@echo "  === python based tests ==="
	@echo "  python-tests - run python based tests"
	@echo "  python-tests-wip - run python based tests"
	@echo ""
	@echo "  nox-tests-3-6 - run python tests in python 3.6 venv"
	@echo "  nox-tests-3-8 - run python tests in python 3.8 venv"
	@echo "  nox-tests-3-10 - run python tests in python 3.10 venv"
	@echo ""
	@echo ""

-include make/*

help:: service-help

# FIXME remove when pr-test workflow removed
pr-tests:
	true

pr-tests-default-python:
	(poetry config virtualenvs.create false && poetry install && make python-tests); TEST_EXIT=$$?;\
		poetry config virtualenvs.create true;
		(exit $$TEST_EXIT)

pr-tests-docker:
	make docker-tests

python-tests:
	pytest

python-tests-wip:
	pytest -m wip --pdb

nox-tests-3-6:
	nox --noxfile repomanager/tests/noxfile.py --python 3.6

nox-tests-3-8:
	nox --noxfile repomanager/tests/noxfile.py --python 3.8

nox-tests-3-10:
	nox --noxfile repomanager/tests/noxfile.py --python 3.10

docker-tests:
	make docker-tests-down; \
		make docker-tests-build && \
		make docker-tests-run; \
		TEST_EXIT=$$?; \
		make docker-tests-down; \
		(exit $$TEST_EXIT)

docker-tests-build:
	${DOCKER_COMPOSE_TEST_COMMAND} build --build-arg CODEARTIFACT_TOKEN=${CODEARTIFACT_TOKEN}

docker-tests-down:
	${DOCKER_COMPOSE_TEST_COMMAND} down

docker-tests-run:
	${DOCKER_COMPOSE_TEST_COMMAND} run repo-manager-tests

docker-tests-run-bash:
	${DOCKER_COMPOSE_TEST_COMMAND} run repo-manager-tests bash

.EXPORT_ALL_VARIABLES:

PROJECT_NAME?="$(shell sed -n 's,^name = \(.*\),\1,p' METADATA)"
VERSION?="$(shell sed -n 's,^version = \(.*\),\1,p' METADATA)"

COMPOSE_ENVIRONMENT="$(or $(COMPOSE_ENV),override)"
COMPOSE_PATH_SEPARATOR?=":"
COMPOSE_FILE?="docker-compose.yml:docker-compose.${COMPOSE_ENVIRONMENT}.yml"
COMPOSE_COMMAND=docker-compose -f docker-compose.yml -f docker-compose.${COMPOSE_ENVIRONMENT}.yml ${DEBUG:+--verbose}

DOCKER_REGISTRY="178847878690.dkr.ecr.us-east-1.amazonaws.com"
DOCKER_API_IMAGE?="${DOCKER_REGISTRY}/${PROJECT_NAME}:${VERSION}"

HELM_VALUES_FILE?="values.yaml"
HELM_CHART_PATH?="deploy/kubernetes/helm/screening-workers"
HELM_RELEASE_NAME="screening-workers"
HELM_NAMESPACE?="testing"

# CodeArtifact envs
# PIP
CODEARTIFACT_AUTH_TOKEN = $(shell aws codeartifact get-authorization-token --domain test-domain --domain-owner 178847878690 --query authorizationToken --output text)

# Twine
TWINE_USERNAME = aws
TWINE_PASSWORD = $(shell aws codeartifact get-authorization-token --domain test-domain --domain-owner 178847878690 --query authorizationToken --output text)
TWINE_REPOSITORY_URL = $(shell aws codeartifact get-repository-endpoint --domain test-domain --domain-owner 178847878690 --repository polestar-pypi-store --format pypi --query repositoryEndpoint --output text)

# General commands

default:
	@echo "Targets:"
	@echo ""
	@echo "$(shell grep -o "^[a-z-]*:[ ]\{0,1\}" Makefile | sed -e "s/://g")"

checkTest:
	@if [ "${COMPOSE_ENVIRONMENT}" != "test" ]; then \
		echo "Not test environment. Exiting"; \
		return 1; \
	fi

params:
	@echo "User: $(shell whoami)"
	@echo "Project name: ${PROJECT_NAME}"
	@echo "Version: ${VERSION}"
	@echo "Compose environment: ${COMPOSE_ENVIRONMENT}"
	@echo "Docker registry: ${DOCKER_REGISTRY}"
	@echo "Docker API image: ${DOCKER_API_IMAGE}"
	@echo "Docker RPM image: ${DOCKER_REGISTRY}/rpm-builder:${VERSION}"
	@echo "Compose command: ${COMPOSE_COMMAND}"
	@echo "AWS CodeArtifact Token: ${CODEARTIFACT_AUTH_TOKEN}"
	@echo "Twine User: ${TWINE_USERNAME}"
	@echo "Twin Password: ${TWINE_PASSWORD}"
	@echo "Twine Repository URL: ${TWINE_REPOSITORY_URL}"
	@docker -v
	@docker-compose -v

# Docker compose commands

compose-ps:
	@${COMPOSE_COMMAND} ps

compose-build:
	@${COMPOSE_COMMAND} build \
		--build-arg CODEARTIFACT_AUTH_TOKEN="${CODEARTIFACT_AUTH_TOKEN}" consumers

compose-prepare: checkTest
	@${COMPOSE_COMMAND} run --rm workers
	@${COMPOSE_COMMAND} up -d consumers
	@${COMPOSE_COMMAND} exec -T consumers python -m pip install -r requirements_dev.txt

compose-logs:
	@${COMPOSE_COMMAND} logs --tail=20 consumers producer

compose-test-python:
	@${COMPOSE_COMMAND} exec -T consumers python setup.py test

compose-clean-pytest-cache:
	@${COMPOSE_COMMAND} exec -T consumers rm -rf .pytest_cache

compose-clean-reports:
	@${COMPOSE_COMMAND} exec -T consumers rm -rf reports

compose-test-cleanup: compose-clean-pytest-cache compose-clean-reports

compose-dist-build:
	@${COMPOSE_COMMAND} exec -T consumers python setup.py bdist_wheel
	@${COMPOSE_COMMAND} exec -T consumers chown 995:992 dist/*.whl

compose-dist-cleanup:
	@${COMPOSE_COMMAND} exec -T consumers rm -rf build/bdist.linux-x86_64 build/lib build/scripts-3.* dist screening_workers.egg-info

compose-dist-upload:
	@${COMPOSE_COMMAND} exec -T consumers twine upload --verbose dist/*.whl

compose-cleanup: compose-test-cleanup compose-dist-cleanup

compose-up:
	@${COMPOSE_COMMAND} up -d consumers

compose-down:
	@${COMPOSE_COMMAND} down -v --rmi local --remove-orphans

#  Docker build commands

docker-login:
	@aws ecr get-login-password --region us-east-1 | docker login -u AWS --password-stdin ${DOCKER_REGISTRY}
	# Uncomment the below if we really need to access dockerhub but we should
	# be caching public images in ECR.
	# docker login -u psalistair -p passpasspass

docker-tag:
	@docker tag ${PROJECT_NAME}:${VERSION} ${DOCKER_API_IMAGE}
	# docker tag $$(${COMPOSE_COMMAND} images -q api) ${DOCKER_API_IMAGE}

docker-untag:
	docker tag ${DOCKER_API_IMAGE} ${PROJECT_NAME}:${VERSION}

docker-build:
	@echo "\e[44mBuilding a base image...\e[0m"
	@docker build --build-arg CODEARTIFACT_AUTH_TOKEN="${CODEARTIFACT_AUTH_TOKEN}" \
		-f docker/Dockerfile . -t ${DOCKER_API_IMAGE}

docker-pull: docker-login
	@docker pull ${DOCKER_API_IMAGE}

docker-push: docker-login
	@docker push ${DOCKER_API_IMAGE}

docker-image:
	@${COMPOSE_COMMAND} images -q | head -n 1

docker-build-compose-deps:
	@echo "\e[44mBuilding Python...\e[0m"
	@docker pull python:3.6-alpine3.10
	@docker tag python:3.6-alpine3.10 "${DOCKER_REGISTRY}/python:3.6-alpine3.10"
	@echo "\e[44mBuilding Redis...\e[0m"
	@docker pull library/redis:4.0.2-alpine
	@docker tag redis:4.0.2-alpine "${DOCKER_REGISTRY}/redis:4.0.2-alpine"
	@echo "\e[44mBuilding RabbitMq...\e[0m"
	@docker pull library/rabbitmq:3.7-management-alpine
	@docker tag rabbitmq:3.7-management-alpine "${DOCKER_REGISTRY}/rabbitmq:3.7-management-alpine"
	@echo "\e[44mBuilding Statsd...\e[0m"
	@docker pull graphiteapp/graphite-statsd:1.1.7-8
	@docker tag graphiteapp/graphite-statsd:1.1.7-8 "${DOCKER_REGISTRY}/graphiteapp/graphite-statsd:1.1.7-8"
	@echo "\e[44mBuilding Postgres...\e[0m"
	@docker pull library/postgres:9.6.5-alpine
	@docker tag postgres:9.6.5-alpine "${DOCKER_REGISTRY}/postgres:9.6.5-alpine"
	@echo "\e[44mBuilding dockerize...\e[0m"
	@docker pull jwilder/dockerize:0.6.1
	@docker tag jwilder/dockerize:0.6.1 "${DOCKER_REGISTRY}/jwilder/dockerize:0.6.1"

docker-push-compose-deps: docker-login
	@docker push "${DOCKER_REGISTRY}/python:3.6-alpine3.10"
	@docker push "${DOCKER_REGISTRY}/redis:4.0.2-alpine"
	@docker push "${DOCKER_REGISTRY}/rabbitmq:3.7-management-alpine"
	@docker push "${DOCKER_REGISTRY}/graphiteapp/graphite-statsd:1.1.7-8"
	@docker push "${DOCKER_REGISTRY}/postgres:9.6.5-alpine"
	@docker push "${DOCKER_REGISTRY}/jwilder/dockerize:0.6.1"

docker-update-compose-deps: docker-build-compose-deps docker-push-compose-deps

clean-image:
	@rm -rf images

# Dist commands

dist-upload:
	@twine upload --verbose dist/*.whl

dist-build:
	@python3 setup.py bdist_wheel

dist-cleanup:
	@rm -rf build/bdist.linux-x86_64 build/lib build/scripts-3.* dist screening_workers.egg-info

# Helm commands

helm-test:
	@helm lint ${HELM_CHART_PATH}

helm-init-client:
	@helm init --client-only

helm-upgrade:
	@helm upgrade --install --wait --set image.tag=${VERSION} \
		${HELM_RELEASE_NAME} ${HELM_CHART_PATH} --namespace ${HELM_NAMESPACE} \
		-f ${HELM_VALUES_FILE}

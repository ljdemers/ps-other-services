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
HELM_CHART_PATH?="deploy/kubernetes/helm/screening-api"
HELM_RELEASE_NAME="screening-api"
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
		exit 1; \
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
	${COMPOSE_COMMAND} ps

compose-build:
	@${COMPOSE_COMMAND} build \
		--build-arg CODEARTIFACT_AUTH_TOKEN="${CODEARTIFACT_AUTH_TOKEN}" api

compose-prepare: checkTest
	@${COMPOSE_COMMAND} run --rm api-proxy-dep
	@${COMPOSE_COMMAND} run --rm api-migrate
	@${COMPOSE_COMMAND} up -d api
	@${COMPOSE_COMMAND} exec -T api python -m pip install -r requirements_dev.txt

compose-logs:
	@${COMPOSE_COMMAND} logs --tail=20 api

compose-test-python:
	@${COMPOSE_COMMAND} exec -T api python setup.py test

compose-test-postman: checkTest
	@${COMPOSE_COMMAND} run --rm api-postman

compose-clean-pytest-cache:
	@${COMPOSE_COMMAND} exec -T api rm -rf .pytest_cache

compose-clean-reports:
	@${COMPOSE_COMMAND} exec -T api rm -rf reports

compose-test-cleanup: compose-clean-pytest-cache compose-clean-reports

compose-dist-build:
	@${COMPOSE_COMMAND} exec -T api python setup.py bdist_wheel
	@${COMPOSE_COMMAND} exec -T api chown 995:992 dist/*.whl

compose-dist-cleanup:
	@${COMPOSE_COMMAND} exec -T api rm -rf build/bdist.linux-x86_64 build/lib build/scripts-3.* dist screening_api.egg-info

compose-dist-upload:
	@${COMPOSE_COMMAND} exec -T api twine upload --verbose dist/*.whl

compose-up:
	@${COMPOSE_COMMAND} up -d api

compose-down:
	@${COMPOSE_COMMAND} down -v --rmi local --remove-orphans

# Docker build commands

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

docker-rpm-build:
	@echo "\e[44mBuilding rpm-builder...\e[0m"
	@docker build -f docker/Dockerfile.rpm-builder . -t "${DOCKER_REGISTRY}/rpm-builder:${VERSION}"

docker-pull: docker-login
	@docker pull ${DOCKER_API_IMAGE}

docker-push: docker-login
	@docker push ${DOCKER_API_IMAGE}

docker-rpm-push:
	@docker push "${DOCKER_REGISTRY}/rpm-builder:${VERSION}"

docker-rpm-pull:
	@docker pull "${DOCKER_REGISTRY}/rpm-builder:${VERSION}"

docker-build-compose-deps:
	@echo "\e[44mBuilding Python...\e[0m"
	@docker pull python:3.6-alpine3.10
	@docker tag python:3.6-alpine3.10 "${DOCKER_REGISTRY}/python:3.6-alpine3.10"
	@echo "\e[44mBuilding Alpine Linux...\e[0m"
	@docker pull alpine:3.6
	@docker tag alpine:3.6 "${DOCKER_REGISTRY}/alpine:3.6"
	@echo "\e[44mBuilding Redis...\e[0m"
	@docker pull library/redis:3.2.12-alpine
	@docker tag redis:3.2.12-alpine "${DOCKER_REGISTRY}/redis:3.2.12-alpine"
	@echo "\e[44mBuilding Newman...\e[0m"
	@docker pull postman/newman_ubuntu1404:3.8.3
	@docker tag postman/newman_ubuntu1404:3.8.3 "${DOCKER_REGISTRY}/newman_ubuntu1404:3.8.3"
	@echo "\e[44mBuilding PGAdmin...\e[0m"
	@docker pull dpage/pgadmin4:3.6
	@docker tag dpage/pgadmin4:3.6 "${DOCKER_REGISTRY}/dpage/pgadmin4:3.6"
	@echo "\e[44mBuilding Postgres...\e[0m"
	@docker pull library/postgres:9.6.5-alpine
	@docker tag postgres:9.6.5-alpine "${DOCKER_REGISTRY}/postgres:9.6.5-alpine"
	@echo "\e[44mBuilding Swagger...\e[0m"
	@docker pull swaggerapi/swagger-ui:v3.4.0
	@docker tag swaggerapi/swagger-ui:v3.4.0 "${DOCKER_REGISTRY}/swagger-ui:v3.4.0"
	@echo "\e[44mBuilding dockerize...\e[0m"
	@docker pull jwilder/dockerize:0.6.1
	@docker tag jwilder/dockerize:0.6.1 "${DOCKER_REGISTRY}/jwilder/dockerize:0.6.1"

docker-push-compose-deps: docker-login
	@docker push "${DOCKER_REGISTRY}/python:3.6-alpine3.10"
	@docker push "${DOCKER_REGISTRY}/alpine3.6"
	@docker push "${DOCKER_REGISTRY}/redis:3.2.12-alpine"
	@docker push "${DOCKER_REGISTRY}/newman_ubuntu1404:3.8.3"
	@docker push "${DOCKER_REGISTRY}/dpage/pgadmin4:3.6"
	@docker push "${DOCKER_REGISTRY}/postgres:9.6.5-alpine"
	@docker push "${DOCKER_REGISTRY}/swagger-ui:v3.4.0"
	@docker push "${DOCKER_REGISTRY}/jwilder/dockerize:0.6.1"

docker-update-compose-deps: docker-build-compose-deps docker-push-compose-deps

clean-image:
	@rm -rf images

# Dist commands

dist-build:
	@python3 setup.py bdist_wheel

dist-cleanup:
	@rm -rf build/bdist.linux-x86_64 build/lib build/scripts-3.* dist screening_api.egg-info

dist-upload:
	@twine upload --verbose dist/*.whl

# Helm commands

helm-test:
	@helm lint ${HELM_CHART_PATH}

helm-init-client:
	@helm init --client-only

helm-check-values-file:
	@if [[ ! -f ${HELM_VALUES_FILE} ]]; then \
		echo "${HELM_VALUES_FILE} file not found. Please provide HELM_VALUES_FILE with values yaml file path"; \
		exit 1; \
	fi

helm-upgrade: helm-check-values-file
	@helm upgrade --install --wait --atomic --recreate-pods --set \
		image.tag=${VERSION} ${HELM_RELEASE_NAME} ${HELM_CHART_PATH} \
		--namespace ${HELM_NAMESPACE} -f ${HELM_VALUES_FILE}

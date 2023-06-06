.EXPORT_ALL_VARIABLES:

PROJECT_NAME=$(shell awk -F '=' '{if (! ($$0 ~ /^;/) && $$0 ~ /^name/) print $$2}' METADATA | tr -d ' ')
VERSION=$(shell awk -F '=' '{if (! ($$0 ~ /^;/) && $$0 ~ /^version/) print $$2}' METADATA | tr -d ' ')
COMPOSE_ENVIRONMENT=$(or $(COMPOSE_ENV),override)
COMPOSE_COMMAND=docker-compose -f docker-compose.yml -f docker-compose.${COMPOSE_ENVIRONMENT}.yml
DOCKER_REGISTRY?=178847878690.dkr.ecr.us-east-1.amazonaws.com

SONAR_HOST_URL?=http://sonarqube.sd.polestar-testing.com:8080
SONAR_LOGIN?=c0ad81cda0f5823f47e6c82b7b862d30979fcd20


default:
	@echo ""
	@echo "Targets:"
	@echo ""
	@echo "  params                 Print parameters"
	@echo "  compose-build          Build image"
	@echo ""

checkTest:
	@if [ "${COMPOSE_ENVIRONMENT}" != "test" ]; then \
		echo "Not test environment. Exiting"; \
		return 1; \
	fi

params:
	@echo "User: $(whoami)"
	@echo "Project name: ${PROJECT_NAME}"
	@echo "Version: ${VERSION}"
	@echo "Compose environment: ${COMPOSE_ENVIRONMENT}"
	@echo "Docker registry: ${DOCKER_REGISTRY}"

compose-ps:
	@${COMPOSE_COMMAND} ps

compose-build:
	@${COMPOSE_COMMAND} build --no-cache sis-api

compose-prepare: checkTest
	@${COMPOSE_COMMAND} run --rm api-dep uname -a

compose-logs:
	@${COMPOSE_COMMAND} logs --tail=20 sis-api

compose-test-python-reports:
	@${COMPOSE_COMMAND} exec -T sis-api mkdir -p reports
	@${COMPOSE_COMMAND} exec -T sis-api chmod 777 reports

compose-test-python:
	@${COMPOSE_COMMAND} exec -T sis-api python manage.py test

compose-permissions-restore:
	@${COMPOSE_COMMAND} exec -T sis-api bin/restore_permissions.sh

compose-test-cleanup:
	@${COMPOSE_COMMAND} exec -T sis-api rm -rf .pytest_cache

compose-dist-build:
	@${COMPOSE_COMMAND} exec -T sis-api python setup.py bdist_wheel
	@${COMPOSE_COMMAND} exec -T sis-api chown 995:992 dist/*.whl

compose-dist-cleanup:
	@${COMPOSE_COMMAND} exec -T sis-api rm -rf build dist

compose-up:
	@${COMPOSE_COMMAND} up -d sis-api

compose-down:
	@${COMPOSE_COMMAND} down -v --rmi local --remove-orphans

docker-image:
	@${COMPOSE_COMMAND} images -q | head -n 1

docker-tag:
	@docker tag ${PROJECT_NAME}:${VERSION} ${DOCKER_REGISTRY}/${PROJECT_NAME}:${VERSION}

docker-push:
	@aws ecr get-login-password --region us-east-1 | docker login -u AWS --password-stdin ${DOCKER_REGISTRY}
	@docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}:${VERSION}

dist-upload:
	@twine upload -r testing dist/*.whl

docker-login:
	@aws ecr get-login-password --region us-east-1 | docker login -u AWS --password-stdin ${DOCKER_REGISTRY}
	# Uncomment the below if we really need to access dockerhub but we should be caching public images in ECR
	# docker login -u psalistair -p passpasspass

docker-build-compose-deps:
	@docker pull python:3.6-alpine
	@docker tag python:3.6-alpine "${DOCKER_REGISTRY}/python:3.6-alpine"
	@docker pull mdillon/postgis:9.6-alpine
	@docker tag mdillon/postgis:9.6-alpine "${DOCKER_REGISTRY}/mdillon/postgis:9.6-alpine"
	@docker pull library/redis:3.2.12-alpine
	@docker tag library/redis:3.2.12-alpine "${DOCKER_REGISTRY}/redis:3.2.12-alpine"
	@docker pull busybox:1.32
	@docker tag busybox:1.32 "${DOCKER_REGISTRY}/busybox:1.32"

docker-push-compose-deps: docker-login
	@docker push "${DOCKER_REGISTRY}/python:3.6-alpine"
	@docker push "${DOCKER_REGISTRY}/mdillon/postgis:9.6-alpine"
	@docker push "${DOCKER_REGISTRY}/redis:3.2.12-alpine"
	@docker push "${DOCKER_REGISTRY}/busybox:1.32"

docker-update-compose-deps: docker-build-compose-deps docker-push-compose-deps

sonarqube-scan: docker-login
		@docker run -e SONAR_LOGIN="${SONAR_LOGIN}" -e SONAR_HOST_URL="${SONAR_HOST_URL}" -v "${PWD}:/usr/src" "${DOCKER_REGISTRY}/sonarsource/sonar-scanner-cli"

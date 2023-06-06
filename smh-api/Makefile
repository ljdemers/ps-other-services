.EXPORT_ALL_VARIABLES:

PROJECT_NAME=$(shell awk -F '=' '{if (! ($$0 ~ /^;/) && $$0 ~ /^name/) print $$2}' METADATA | tr -d ' ')
VERSION=$(shell awk -F '=' '{if (! ($$0 ~ /^;/) && $$0 ~ /^version/) print $$2}' METADATA | tr -d ' ')
COMPOSE_ENVIRONMENT=$(or $(COMPOSE_ENV),override)
COMPOSE_COMMAND=docker-compose -f docker-compose.yml -f docker-compose.${COMPOSE_ENVIRONMENT}.yml ${DEBUG:+--verbose}

DOCKER_REGISTRY?=178847878690.dkr.ecr.us-east-1.amazonaws.com
DOCKER_VERSION?=${VERSION}
DOCKER_API_IMAGE?=${DOCKER_REGISTRY}/purpletrac-api:${DOCKER_VERSION}

REPORTS_DIR=reports
REPORTS_JUNIT=${REPORTS_DIR}/junit.xml
REPORTS_COVERAGE=${REPORTS_DIR}/coverage.xml
HTML_REPORTS=${REPORTS_DIR}/html

default:
	@echo ""
	@echo "Targets:"
	@echo ""
	@echo "  params                 Print parameters"
	@echo "  compose-build          Build docker image"
	@echo ""

checkTest:
	@if [ "${COMPOSE_ENVIRONMENT}" != "test" ]; then \
		echo "Not test environment. Exiting"; \
		exit 1; \
	fi

params:
	@echo "User: $(whoami)"
	@echo "Project name: ${PROJECT_NAME}"
	@echo "Version: ${VERSION}"
	@echo "Compose environment: ${COMPOSE_ENVIRONMENT}"

compose-ps:
	@${COMPOSE_COMMAND} ps

compose-build:
	@${COMPOSE_COMMAND} build

compose-prepare: checkTest
	@${COMPOSE_COMMAND} run --rm smh-dep uname -a

compose-logs:
	@${COMPOSE_COMMAND} logs --tail=50 smh-api

compose-test-python:
	@${COMPOSE_COMMAND} exec -T smh-api pytest ..

compose-up:
	@${COMPOSE_COMMAND} up

compose-down:
	@${COMPOSE_COMMAND} down -v --rmi local --remove-orphans

clean-image:
	rm -rfv images

clean: clean-image

docker-login:
	@$$(aws ecr get-login --region us-east-1 --no-include-email)
	# Uncomment the below if we really need to access dockerhub but we should be caching public images in ECR
	# docker login -u psalistair -p passpasspass

docker-tag:
	docker tag $$(${COMPOSE_COMMAND} images -q api) ${DOCKER_API_IMAGE}

docker-pull: docker-login
	@docker pull ${DOCKER_API_IMAGE}

docker-push: docker-login
	@docker push ${DOCKER_API_IMAGE}

docker-base-push: docker-login
	@docker push "${DOCKER_REGISTRY}/purpletrac-base:2020-11"

docker-build-compose-deps:
	@docker pull python:3.6-slim-buster
	@docker tag python:3.6-slim-buster "${DOCKER_REGISTRY}/python:3.6-slim-buster"
	@docker pull postgres:11.5-alpine
	@docker tag postgres:11.5-alpine "${DOCKER_REGISTRY}/postgres:11.5-alpine"
	@docker pull busybox:1.32
	@docker tag busybox:1.32 "${DOCKER_REGISTRY}/busybox:1.32"

docker-push-compose-deps: docker-login
	@docker push "${DOCKER_REGISTRY}/python:3.6-slim-buster"
	@docker push "${DOCKER_REGISTRY}/postgres:11.5-alpine"
	@docker push "${DOCKER_REGISTRY}/busybox:1.32"

docker-update-compose-deps: docker-build-compose-deps docker-push-compose-deps

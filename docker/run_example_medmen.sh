#!/usr/bin/env bash

DOCKER_COMPOSE_FILE="docker-compose.example-medmen.yml"
# To run in a container run "export LOCALHOST_NAME=host.docker.internal"
LOCALHOST_NAME=${LOCALHOST_NAME:-localhost}

echo "Running docker-compose"
docker compose -f ${DOCKER_COMPOSE_FILE} up -d

echo "Running test"
source ../scripts/integration_test_functions.sh
smoketest_medcat_service $LOCALHOST_NAME $DOCKER_COMPOSE_FILE
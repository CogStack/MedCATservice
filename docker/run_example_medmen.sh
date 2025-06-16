#!/usr/bin/env bash


# ( cd ../scripts && bash download_medmen.sh )

echo "Running docker-compose"
DOCKER_COMPOSE_FILE="docker-compose-example-medmen.yml"
docker compose -f ${DOCKER_COMPOSE_FILE} up -d


source ../scripts/smoketest.sh
smoketest_medcat_service "host.docker.internal" $DOCKER_COMPOSE_FILE
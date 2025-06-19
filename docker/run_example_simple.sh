#!/usr/bin/env bash

DOCKER_COMPOSE_FILE="docker-compose.example.yml"
# To run in a container run "export LOCALHOST_NAME=host.docker.internal"
LOCALHOST_NAME=${LOCALHOST_NAME:-localhost}

echo "Running docker-compose"
docker compose -f ${DOCKER_COMPOSE_FILE} up -d

echo "Running test"
source ../scripts/integration_test_functions.sh
smoketest_medcat_service $LOCALHOST_NAME $DOCKER_COMPOSE_FILE

if [ $? -ne 0 ]; then
    echo "Failed basic smoketest"
    exit 1
fi

# Test the deployment
integration_test_medcat_service $LOCALHOST_NAME
if [ $? -ne 0 ]; then
    echo "Failed integration test"
    exit 1
fi

cat <<EOF
-----------------------------------------------------------------
MedCATService running on http://${LOCALHOST_NAME}:5555/
-----------------------------------------------------------------
EOF
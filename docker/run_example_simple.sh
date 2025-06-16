#!/usr/bin/env bash
set -e

DOCKER_COMPOSE_FILE="docker-compose.example.yml"
# To run in a container run "export LOCALHOST_NAME=host.docker.internal"
LOCALHOST_NAME=${LOCALHOST_NAME:-localhost}

echo "Running docker-compose"
docker compose -f ${DOCKER_COMPOSE_FILE} up -d

echo "Running test"
source ../scripts/smoketest.sh
smoketest_medcat_service $LOCALHOST_NAME $DOCKER_COMPOSE_FILE

# Test the deployment

INPUT_TEXT="The patient was diagnosed with Kidney Failure"
EXPECTED_ANNOTATION="Kidney Failure"
ACTUAL=$(curl -s -X POST "http://${LOCALHOST_NAME}:5555/api/process" \
  -H 'Content-Type: application/json' \
  -d "{\"content\":{\"text\":\"${INPUT_TEXT}\"}}")

# Extract the first annotation's pretty_name using jq
ACTUAL_ANNOTATION=$(echo "$ACTUAL" | jq -r '.result.annotations[0]["0"].pretty_name')

if [[ "$ACTUAL_ANNOTATION" == "$EXPECTED_ANNOTATION" ]]; then
  echo "Service working and extracting annotations"
else
  echo "Expected: $EXPECTED_ANNOTATION, Got: $ACTUAL_ANNOTATION"
  echo "Actual response was \n${ACTUAL}"
  exit 1
fi
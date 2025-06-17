#!/bin/bash
# Integration test of medcat service docker image

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${SCRIPT_DIR}/../docker
bash run_example_simple.sh

docker compose -f docker-compose.example.yml down

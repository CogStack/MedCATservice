#!/usr/bin/env bash
set -e

( cd ../models && bash download_medmen.sh )

echo "Running docker-compose"
docker-compose -f docker-compose.yml up

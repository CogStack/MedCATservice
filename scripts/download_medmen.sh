#!/usr/bin/env bash
set -e

export MODEL_NAME=medmen
export MODEL_VOCAB_URL=https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/vocab.dat 
export MODEL_CDB_URL=https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/cdb-medmen-v1.dat 
export MODEL_META_URL=https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/mc_status.zip 
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

bash ${SCRIPT_DIR}/download_model.sh
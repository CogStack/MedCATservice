#!/bin/bash
set -e

# model files
MODEL_CDB=../models/cdb.dat
MODEL_VCB=../models/vcb.dat

if [[ ! -f "$MODEL_CDB"  || ! -f "$MODEL_VCB" ]]; then
  echo "Downloading models: MedMentions"
  # download the models as described in the MedCAT repo
  curl https://s3-eu-west-1.amazonaws.com/zkcl/vocab.dat > $MODEL_VCB
  curl https://s3-eu-west-1.amazonaws.com/zkcl/cdb-medmen-clean.dat > $MODEL_CDB
else
  echo "MedMentions models are present -- skipping downloading"
fi

echo "Running docker-compose"
docker-compose up

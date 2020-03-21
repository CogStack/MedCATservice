#!/bin/bash
set -e

# output model files
MEDMEN_DIR=./medmen
MODEL_CDB=$MEDMEN_DIR/cdb.dat
MODEL_VCB=$MEDMEN_DIR/vocab.dat

if [[ ! -f "$MODEL_CDB"  || ! -f "$MODEL_VCB" ]]; then
  echo "Downloading models: MedMentions"
  if [[ ! -d $MEDMEN_DIR ]]; then
    mkdir $MEDMEN_DIR
  fi
  # download the models as described in the MedCAT repo
  curl https://s3-eu-west-1.amazonaws.com/zkcl/vocab.dat > $MODEL_VCB
  curl https://s3-eu-west-1.amazonaws.com/zkcl/cdb-medmen.dat > $MODEL_CDB
else
  echo "MedMentions models are present -- skipping downloading"
fi

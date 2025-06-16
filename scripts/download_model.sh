#!/usr/bin/env bash
set -e

: "${MODEL_NAME:?You must set MODEL_NAME}"
: "${MODEL_VOCAB_URL:?You must set MODEL_VOCAB_URL}"
: "${MODEL_CDB_URL:?You must set MODEL_CDB_URL}"
: "${MODEL_META_URL:?You must set MODEL_META_URL}"

# output model files
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR=${SCRIPT_DIR}/../models/${MODEL_NAME}
MODEL_CDB_FILE=$MODEL_DIR/cdb.dat
MODEL_VOCAB_FILE=$MODEL_DIR/vocab.dat
MODEL_META_OUTPUT_FILE=$MODEL_DIR/mc_status.zip
MODEL_META_OUTPUT_DIR=$MODEL_DIR/Status

if [[ ! -d $MODEL_DIR ]]; then
  mkdir $MODEL_DIR
fi

if [[  -f "$MODEL_CDB_FILE"  && -f "$MODEL_VOCAB_FILE" ]]; then
  echo "${MODEL_NAME} model already present -- skipping download"
fi

if [[ ! -f "$MODEL_VOCAB_FILE" ]]; then
  echo "Downloading vocab from ${MODEL_VOCAB_URL}"
  curl -o "$MODEL_VOCAB_FILE" ${MODEL_VOCAB_URL}
fi

if [[ ! -f "$MODEL_CDB_FILE" ]]; then
  echo "Downloading CDB from ${MODEL_CDB_URL}"
  curl -o "$MODEL_CDB_FILE" ${MODEL_CDB_URL}
fi


if [[ ! -d "$MODEL_META_OUTPUT_DIR" ]]; then
  echo "Downloading meta model: status"
   curl -o "$MODEL_META_OUTPUT_FILE" ${MODEL_META_URL} > $MODEL_DIR/mc_status.zip && \
    (unzip ${MODEL_META_OUTPUT_FILE}) && \
    rm $MODEL_META_OUTPUT_FILE
else
  echo "Meta model already present -- skipping download"
fi

 echo "Completed downloading model ${MODEL_NAME}"

#!/bin/bash
set -e

# download the sci-scpacy language model
python3 -m pip install -r ./requirements.txt
python3 -m spacy download en_core_web_sm
python3 -m spacy download en_core_web_md
python3 -m spacy download en_core_web_lg

# download the test MedCAT model
( cd ./models && bash download_medmen.sh )
export APP_CDB_MODEL="$PWD/models/medmen/cdb.dat"
export APP_VOCAB_MODEL="$PWD/models/medmen/vocab.dat"

# proceed with the tests
#
echo "Starting the tests ..."

# run the python tests
python3 -m medcat_service.test.test_service

if [ "$?" -ne "0" ]; then
    echo "Error: one or more tests failed"
    exit 1
fi

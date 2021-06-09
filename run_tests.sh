#!/bin/bash
set -e

# download the sci-scpacy language model
python -m spacy download en_core_web_md
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.3.0/en_core_sci_md-0.3.0.tar.gz

# download the test MedCAT model
( cd ./models && bash download_medmen.sh )
export APP_CDB_MODEL="$PWD/models/medmen/cdb.dat"
export APP_VOCAB_MODEL="$PWD/models/medmen/vocab.dat"

# proceed with the tests
#
echo "Starting the tests ..."

# run the python tests
python -m medcat_service.test.test_service

if [ "$?" -ne "0" ]; then
    echo "Error: one or more tests failed"
    exit 1
fi

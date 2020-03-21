#!/bin/bash
set -e

# check the requirements
#
echo "Checking the requirements ..."

# assumes that python virtualenv module is installed
# otherwise: pip install virtualenv
python -c "import virtualenv"
if [ "$?" -ne "0" ]; then
    echo "Error: Python virtualenv module not available"
    exit 1
fi

# create a python virtual environment and install the necessary packages
#
python -m virtualenv venv-test
source venv-test/bin/activate
pip install -r medcat_service/requirements.txt

# download the sci-scpacy language model
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.3/en_core_sci_md-0.2.3.tar.gz

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

# finish
deactivate
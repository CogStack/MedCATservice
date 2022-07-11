FROM python:3.7-slim

# Set the python path and preapre the base layer
WORKDIR /cat
COPY ./medcat_service/requirements.txt /cat
RUN pip install --upgrade pip

# Install requirements for the app
RUN pip install -r requirements.txt

# Get the spacy model
ARG SPACY_MODELS="en_core_web_sm en_core_web_md en_core_web_lg"
RUN for spacy_model in ${SPACY_MODELS}; do python -m spacy download $spacy_model; done

# Copy the remaining files
COPY . /cat

# Now run the simple api
CMD ["/bin/bash", "start-service-prod.sh"]

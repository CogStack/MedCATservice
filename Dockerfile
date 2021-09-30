FROM python:3.7-slim

# Set the python path and preapre the base layer
WORKDIR /cat
COPY ./medcat_service/requirements.txt /cat
RUN pip install --upgrade pip

# Install requirements for the app
RUN pip install -r requirements.txt

# Get the spacy model
RUN python -m spacy download en_core_web_md     
RUN python -m spacy download en_core_web_lg

RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.4.0/en_core_sci_md-0.4.0.tar.gz
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.4.0/en_core_sci_lg-0.4.0.tar.gz

# Copy the remaining files
COPY . /cat

# Now run the simple api
CMD ["/bin/bash", "start-service-prod.sh"]

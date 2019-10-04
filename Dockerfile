FROM python:3.7-slim

# Set the pythonpath and preapre the base layer
WORKDIR /cat
COPY ./medcat_service/requirements.txt /cat

# Reqs for the app
RUN pip install -r requirements.txt

# Get the spacy model
#RUN python -m spacy download en_core_web_sm
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_core_sci_md-0.2.0.tar.gz

# copy the remaining files
COPY . /cat

# Now run the simple api
#ENTRYPOINT ["bin/bash"]
CMD ["/bin/bash", "start-service-prod.sh"]

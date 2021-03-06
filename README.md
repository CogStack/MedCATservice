# Introduction

This project implements the [MedCAT](https://github.com/CogStack/MedCAT/) NLP application as a service behind a REST API. The general idea is to be able send the text to MedCAT NLP service and receive back the annotations. The REST API is built using [Flask](https://flask.palletsprojects.com/).


# API specification

The API definition follows the one defined in [CogStack GATE NLP Service](https://github.com/CogStack/gate-nlp-service/). Currently, there are 3 endpoints defined, that consume and return data in JSON format:
- *GET* `/api/info` - displays general information about the MedCAT application,
- *POST* `/api/process` - processes the provided documents and returns back the annotations,
- *POST* `/api/process_bulk` - processes the provided list of documents and returns back the annotations.

The full specification is available is [OpenAPI](https://github.com/CogStack/gate-nlp-service/tree/devel/api-specs) specification.


# Running the application

The application can be run either as a standalone Python application or as running inside the Docker container (recommended).

## Running as a Python app

Please note that prior running the application a number of requirements need to installed (see: `requirements.txt`).

There are two scripts provided implementing starting the application:
- `start-service-dev.sh` - starts the application in the development mode and using `werkzeug` server for serving Flask applications,
- `start-service-prod.sh` - starts the application in 'production' mode and using `gunicorn` server.

## Running in a Docker container

The recommended way to run the application is to use the provided Docker image. The Docker image can be either downloaded from the Docker Hub (`cogstacksystems/medcat-service:latest`) or build manually using the provided `Dockerfile`. 
Please note that by default the built docker image will run the Flask application in 'production' mode running `start-service-prod.sh` script.

To build the Docker image manually:

`docker build -t medcat-service  .`

To run the container using the built image:

```
docker run -it -p 5000:5000 \
  --env-file=envs/env_app --env-file=envs/env_medcat \
  -v <models-local-dir>:/cat/models:ro \
  cogstacksystems/medcat-service:latest
```

By default the MedCAT service will be running on port `5000`. MedCAT models will be mounted from local directory `<models-local-dir>` into the container at `/cat/models`. 

Alternatively, an example script `./docker/run_example_medmen.sh` was provided to run the Docker container with MedCAT service. The script will download an example model (using `./models/download_medmen.sh` script), will use an example environment configuration, build and start the service using the provided Docker Compose file.


# Example use

Assuming that the application is running on the `localhost` with the API exposed on port `5000`, one can run:
```
curl -XPOST http://localhost:5000/api/process \
  -H 'Content-Type: application/json' \
  -d '{"content":{"text":"The patient was diagnosed with leukemia."}}'
```

and the received result:
```
{
  "result": {
    "text": "The patient was diagnosed with leukemia.",
    "annotations": [
      {
        "pretty_name": "leukemia",
        "cui": "C0023418",
        "tui": "T191",
        "type": "Neoplastic Process",
        "source_value": "leukemia",
        "acc": "1",
        "start": 31,
        "end": 39,
        "info": {},
        "id": "0",
        "meta_anns": {}
      }
    ],
    "success": true,
    "timestamp": "2019-12-03T16:09:58.196+00:00"
  }
}
```

Please note that the returned NLP annotations will depend on the underlying model used. For evaluation, we can only provide a very basic model trained on [MedMentions](https://github.com/chanzuckerberg/MedMentions). Models utilising [SNOMED CT](https://www.england.nhs.uk/digitaltechnology/digital-primary-care/snomed-ct/) or [UMLS](https://www.nlm.nih.gov/research/umls/index.html) may require applying for licenses from the copyright holders.


# Configuration

In the current implementation, configuration for both MedCAT Service application and MedCAT NLP library is based on environment variables. These will be provided usually in two files in `env` directory:
- `env_app` - configuration of MedCAT Service app,
- `env_medcat` - configuration of MedCAT library.

Both files allow tailoring MedCAT for specific use-cases. When running MedCAT Service, these variables need to be loaded into the current working environment.

## MedCAT Service
MedCAT Service application are defined in `envs/env_app` file.

The following environment variables are available for tailoring the MedCAT Service `gunicorn` server:
- `SERVER_HOST` - specifies the host address (default: `0.0.0.0`),
- `SERVER_PORT` - the port number used (default: `5000`),
- `SERVER_WORKERS` - the number of workers serving the Flask app working in parallel (default: `1` ; only used in production server).
- `SERVER_WORKER_TIMEOUT` - the max timeout (in sec) for receiving response from worker (default: `300` ; only used with production server).

The following environment variables are available for tailoring the MedCAT Service wrapper:
- `APP_MODEL_NAME` - an informative name of the model used by MedCAT (optional), 
- `APP_MODEL_CDB_PATH` - the path to the model's concept database,
- `APP_MODEL_VOCAB_PATH` - the path to the model's vocabulary,
- `APP_MODEL_META_PATH_LIST` - the list of paths to meta-annotation models, each separated by `:` character (optional),
- `APP_BULK_NPROC` - the number of threads used in bulk processing (default: `8`),
- `APP_TRAINING_MODE` - whether to run the application with MedCAT in training mode (default: `False`).


## MedCAT library
MedCAT parameters are defined in selected `envs/env_medcat*`  file. 

For details on available MedCAT parameters please refer to [the official GitHub repository](https://github.com/CogStack/MedCAT/).

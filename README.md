# Introduction

This project implements the [MedCAT](https://github.com/CogStack/MedCAT/) NLP application as a service behind a REST API. The general idea is to be able send the text to MedCAT NLP service and receive back the annotations. The REST API is using [Flask](https://flask.palletsprojects.com/).


# API specification

The API definition follows the one defined in [CogStack NLP REST Service](https://github.com/CogStack/nlp-rest-service/tree/master/service). Currently, there are 3 endpoints defined, that consume and return data in JSON format:
- *GET* `/api/info` - displays general information about the MedCAT application,
- *POST* `/api/process` - processes the provided documents and returns back the annotations,
- *POST* `/api/process_bulk` - processes the provided list of documents and returns back the annotations.

The full specification is available is [OpenAPI](https://github.com/CogStack/nlp-rest-service/blob/master/service/api-specs/openapi.yaml) specification.


# Running the application

The application can be run either as a standalone Python application or as running inside the Docker container (recommended).

**IMPORTANT:** Please note that the current version of the docker image uses `werkzeug` server for serving Flask applications and should not be used in production.


## Running as a Python app

Please note that prior running the application a number of requirements need to installed (see: `requirements.txt`).

There are two scripts provided implementing starting the application:
- `start-service-dev.sh` - starts the application in the development mode and using `werkzeug` server for serving Flask applications,
- `start-service-prod.sh` - starts the application in 'production' mode and using `gunicorn` server.

These scripts use the following environment variables which are set to default when not specified:
- `SERVER_HOST` - specifies the host address (default: `0.0.0.0`),
- `SERVER_PORT` - the port number used (default: `5000`),
- `SERVER_WORKERS` - the number of workers serving the Flask app working in parallel (default: `1` ; only used in production).

## Running in a Docker container

The recommended way to run the application is to use the provided Docker image. The Docker image can be either downloaded from the Docker Hub (`cogstacksystems/medcatservice:latest`) or build manually using the provided `Dockerfile`. 
Please note that by default the built docker image will run the Flask application in 'production' mode running `start-service-prod.sh` script.

To build the Docker image manually:

`docker build -t medcat-service  .`

To run the container using the built image:

`docker run -it -p 5000:5000 -v <models-local-dir>:/cat/models:ro medcat-service`

By default the MedCAT service will be running on port `5000`.

An example script `./docker/run_example_medmen.sh` was provided to run the Docker container with MedCAT service. The script will download an example model (using `./models/download_medmen.sh` script), will use an example environment configuration and start the service.


# Example use

Assuming that the application is running on the `localhost` with the API exposed on port `5000`, one can run:
```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{'content':{"text": "lung cancer diagnosis"}}' \
  http://localhost:5000/api/process
```

and the received result:
```
{
  "result": {
    "text": "lung cancer diagnosis",
    "annotations": [
      {
        "cui": "C0920688",
        "tui": "T060",
        "type": "Diagnostic Procedure",
        "source_value": "lung cancer diagnosis",
        "acc": "1",
        "start_tkn": 0,
        "end_tkn": 2,
        "start_ind": 0,
        "end_ind": 21,
        "label": "C0920688 - metastatic lung cancer - T060 - Diagnostic Procedure - 1.0",
        "id": "1",
        "pretty_name": "metastatic lung cancer"
      }
    ],
    "success": true
  }
}
```


# Configuration

Currently, both the application and MedCAT configuration is done using a set of environment variables. This way, some internal MedCAT parameters can tailored to specific use-case. Please see `envs` directory for example configuration files.

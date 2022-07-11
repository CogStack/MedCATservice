#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import traceback

import simplejson as json
from flask import Blueprint, Response, request

from medcat_service.nlp_service import NlpService

log = logging.getLogger("API")
log.setLevel(level=os.getenv("APP_LOG_LEVEL", logging.INFO))

# define API using Flask Blueprint
#
api = Blueprint(name='api', import_name='api', url_prefix='/api')


# API endpoints definition
#
# INFO: we use dependency injection to inject the actual NLP (MedCAT) service
#
@api.route('/info', methods=['GET'])
def info(nlp_service: NlpService) -> Response:
    """
    Returns basic information about the NLP Service
    :param nlp_service: NLP Service provided by dependency injection
    :return: Flask Response
    """
    app_info = nlp_service.nlp.get_app_info()
    return Response(response=json.dumps(app_info), status=200, mimetype="application/json")


@api.route('/process', methods=['POST'])
def process(nlp_service: NlpService) -> Response:
    """
    Returns the annotations extracted from a provided single document
    :param nlp_service: NLP Service provided by dependency injection
    :return: Flask response
    """
    payload = request.get_json()
    if payload is None or 'content' not in payload or payload['content'] is None:
        return Response(response="Input Payload should be JSON", status=400)

    try:
        result = nlp_service.nlp.process_content(payload['content'])
        app_info = nlp_service.nlp.get_app_info()
        response = {'result': result, 'medcat_info': app_info}
        return Response(response=json.dumps(response, iterable_as_array=True), status=200, mimetype="application/json")

    except Exception as e:
        log.error(traceback.format_exc())
        return Response(response="Internal processing error %s" % e, status=500)


@api.route('/process_bulk', methods=['POST'])
def process_bulk(nlp_service: NlpService) -> Response:
    """
    Returns the annotations extracted from the provided set of documents
    :param nlp_service: NLP Service provided by dependency injection
    :return: Flask Response
    """
    payload = request.get_json()
    if payload is None or 'content' not in payload.keys() or payload['content'] is None:
        return Response(response="Input Payload should be JSON", status=400)

    try:
        result = nlp_service.nlp.process_content_bulk(payload['content'])
        app_info = nlp_service.nlp.get_app_info()

        response = {'result': result, 'medcat_info': app_info}
        return Response(response=json.dumps(response, iterable_as_array=True), status=200, mimetype="application/json")

    except Exception as e:
        log.error(traceback.format_exc())
        return Response(response="Internal processing error %s" % e, status=500)


@api.route('/retrain_medcat', methods=['POST'])
def retrain_medcat(nlp_service: NlpService) -> Response:

    payload = request.get_json()
    if payload is None or 'content' not in payload or payload['content'] is None:
        return Response(response="Input Payload should be JSON", status=400)

    try:
        result = nlp_service.nlp.retrain_medcat(payload['content'], payload['replace_cdb'])
        app_info = nlp_service.nlp.get_app_info()
        response = {'result': result, 'annotations': payload['content'], 'medcat_info': app_info}
        return Response(response=json.dumps(response), status=200, mimetype="application/json")

    except Exception as e:
        log.error(traceback.format_exc())
        return Response(response="Internal processing error %s" % e, status=500)

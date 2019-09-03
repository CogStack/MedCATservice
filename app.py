from flask import Flask
from flask import Response
from flask import request
import json

from medcat_service import MedCatService

import os
import logging

# global medcat service
#
service_cat = MedCatService()
app = Flask(__name__)


# Flask endpoints definition
#
@app.route('/api/info', methods=['GET'])
def info():
    app_info = service_cat.get_app_info()
    return Response(response=json.dumps(app_info), status=200, mimetype="application/json")


@app.route('/api/process', methods=['POST'])
def process():
    payload = request.get_json()
    if payload is None or 'content' not in payload or payload['content'] is None:
        return Response(response="Input Payload should be JSON", status=400)

    try:
        result, success = service_cat.process_content(payload['content'])
        if success is True:
            status_code = 200
        else:
            status_code = 400

        response = {'result': result}
        return Response(response=json.dumps(response), status=status_code)

    except Exception as e:
        Response(response="Internal processing error %d" % e, status=500)


@app.route('/api/process_bulk', methods=['POST'])
def process_bulk():
    payload = request.get_json()
    if payload is None or 'content' not in payload or payload['content'] is None:
        return Response(response="Input Payload should be JSON", status=400)

    try:
        result, success = service_cat.process_content_bulk(payload['content'])
        if success is True:
            status_code = 200
        else:
            status_code = 400

        response = {'result': result}
        return Response(response=json.dumps(response), status=status_code)

    except Exception as e:
        Response(response="Internal processing error %d" % e, status=500)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

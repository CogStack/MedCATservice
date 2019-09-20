from flask import Flask
from flask import Response
from flask import request

import simplejson as json
import logging
import sys

from medcat_service import MedCatService


def create_app():
    # setup logging
    setup_logging()

    # setup medcat
    service_cat = MedCatService()

    # create flask app
    app = Flask(__name__)

    # define flask endpoints
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
            result = service_cat.process_content(payload['content'])
            response = {'result': result}
            return Response(response=json.dumps(response), status=200)

        except Exception as e:
            Response(response="Internal processing error %d" % e, status=500)

    @app.route('/api/process_bulk', methods=['POST'])
    def process_bulk():
        payload = request.get_json()
        if payload is None or 'content' not in payload or payload['content'] is None:
            return Response(response="Input Payload should be JSON", status=400)

        try:
            result = service_cat.process_content_bulk(payload['content'])
            response = {'result': result}
            return Response(response=json.dumps(response, iterable_as_array=True), status=200)

        except Exception as e:
            Response(response="Internal processing error %d" % e, status=500)

    # remember to return the app
    return app


def setup_logging():
    log_format = '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'

    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(logging.Formatter(fmt=log_format))
    log_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)


# the app main entry point
#
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

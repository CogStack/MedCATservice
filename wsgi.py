#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file is used to create a Flask application that will be served by a WSGI server
"""
from medcat_service.app import create_app

application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)

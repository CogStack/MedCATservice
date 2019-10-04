#!/bin/bash

echo "Running Flask develoment server"
#python -m wsgi

export FLASK_APP=wsgi.py
export FLASK_ENV=development

flask run --host 0.0.0.0 --port 5000
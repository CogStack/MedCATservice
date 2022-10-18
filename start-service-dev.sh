#!/bin/bash

# check the gunicorn config params
#
if [ -z ${SERVER_HOST+x} ]; then
  echo "SERVER_HOST is unset -- setting to default: 0.0.0.0";
  SERVER_HOST=0.0.0.0;
fi

if [ -z ${SERVER_PORT+x} ]; then
  echo "SERVER_PORT is unset -- setting to default: 5000";
  SERVER_PORT=5000;
fi

# start the server
#
echo "Running Flask develoment server"
export FLASK_APP=wsgi.py
export FLASK_DEBUG=true

flask run --host $SERVER_HOST --port $SERVER_PORT

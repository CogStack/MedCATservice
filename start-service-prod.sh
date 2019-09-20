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

if [ -z ${SERVER_WORKERS+x} ]; then
  echo "SERVER_WORKERS is unset -- setting to default: 1";
  SERVER_WORKERS=1;
fi


# start the server
#
echo "Starting up Flask app using gunicorn server ..."
gunicorn --bind $SERVER_HOST:$SERVER_PORT --workers=$SERVER_WORKERS --log-file=- --log-level info wsgi

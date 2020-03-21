#!/bin/bash

# check the gunicorn config params
#
if [ -z ${SERVER_HOST+x} ]; then
  SERVER_HOST=0.0.0.0;
  echo "SERVER_HOST is unset -- setting to default: $SERVER_HOST";
fi

if [ -z ${SERVER_PORT+x} ]; then
  SERVER_PORT=5000;
  echo "SERVER_PORT is unset -- setting to default: $SERVER_PORT";
fi

if [ -z ${SERVER_WORKERS+x} ]; then
  SERVER_WORKERS=1;
  echo "SERVER_WORKERS is unset -- setting to default: $SERVER_WORKERS";
fi

if [ -z ${SERVER_WORKER_TIMEOUT+x} ]; then
  SERVER_WORKER_TIMEOUT=300;
  echo "SERVER_WORKER_TIMEOUT is unset -- setting to default (sec): $SERVER_WORKER_TIMEOUT";
fi


SERVER_ACCESS_LOG_FORMAT="%(t)s [ACCESSS] %(h)s \"%(r)s\" %(s)s \"%(f)s\" \"%(a)s\""

# start the server
#
echo "Starting up Flask app using gunicorn server ..."
gunicorn --bind $SERVER_HOST:$SERVER_PORT --workers=$SERVER_WORKERS --timeout=$SERVER_WORKER_TIMEOUT \
  --access-logformat="$SERVER_ACCESS_LOG_FORMAT" --access-logfile=- --log-file=- --log-level info \
  wsgi
